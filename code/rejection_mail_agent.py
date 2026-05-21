"""
Agent #2: Tự động gửi email TỪ CHỐI khi ứng viên có Tình trạng "Không phù hợp".

Nguồn dữ liệu: https://ngoclinhhrm.com/tuyen-dung/  (qua HRM API)
Endpoint:      https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates

Điều kiện kích hoạt (AND):
  - Tình trạng = "Không phù hợp"
  - rejection_email_status ≠ "sent"  (chưa gửi mail từ chối)
  - Có Email
  - record_id chưa có trong rejection_sent.json

Hành động (theo thứ tự):
  1. Gửi email "Phản hồi kết quả ứng tuyển" (Template 3) qua Lark Mail
  2. Gửi tin Lark IM cho HRM báo
  3. PATCH HRM rejection_email_status=sent
  4. Ghi record vào rejection_sent.json
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# Tận dụng helper từ interview_invite_agent (cùng app, cùng env, cùng token)
from interview_invite_agent import (
    _get_user_token,
    _get_tenant_token,
    send_lark_im,
    fetch_candidates,
    F_ID, F_NAME, F_EMAIL, F_POSITION, F_FIT,
    HRM_API_BASE, HRM_KEY,
    LARK_DOMAIN, SENDER_MAIL,
    _VN_TZ,
)

load_dotenv()
log = logging.getLogger("rejection-agent")

# ─── Tracking ────────────────────────────────────────────────────────────────
SENT_LOG = Path(__file__).parent / "rejection_sent.json"
FIT_NO = "Không phù hợp"


def _load_sent() -> set:
    if SENT_LOG.exists():
        return set(json.loads(SENT_LOG.read_text(encoding="utf-8")))
    return set()


def _save_sent(sent: set) -> None:
    SENT_LOG.write_text(json.dumps(sorted(sent), indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Logic ───────────────────────────────────────────────────────────────────

def is_to_reject(c: dict) -> bool:
    return (
        (c.get(F_FIT) or "").strip() == FIT_NO
        and bool((c.get(F_EMAIL) or "").strip())
        # Skip nếu HRM đã đánh dấu đã gửi
        and (c.get("Email từ chối - Trạng thái") or "") != "sent"
    )


def _build_rejection_html(name: str, position: str) -> str:
    """Template 3 — Từ chối ứng viên (chuẩn SEONGON)."""
    return f"""\
<div style="font-family:Arial,sans-serif;font-size:15px;color:#222;max-width:600px">
<p>Kính gửi anh/chị <b>{name}</b>,</p>

<p>Phòng Tuyển dụng <b>SEONGON</b> xin cảm ơn anh/chị đã quan tâm và ứng tuyển
vị trí <b>{position}</b> tại công ty chúng tôi.</p>

<p>Sau khi xem xét kỹ lưỡng hồ sơ, chúng tôi rất tiếc phải thông báo rằng ở thời điểm
hiện tại, hồ sơ của anh/chị <b>chưa thực sự phù hợp</b> với yêu cầu cụ thể của vị trí này.</p>

<p>SEONGON sẽ lưu lại hồ sơ của anh/chị trong cơ sở dữ liệu và sẽ chủ động liên hệ khi có
vị trí phù hợp hơn trong tương lai. Chúc anh/chị sớm tìm được công việc như ý.</p>

<p>Trân trọng,<br>
<b>Phòng Tuyển dụng - SEONGON</b><br>
Email: <a href="mailto:{SENDER_MAIL}">{SENDER_MAIL}</a><br>
Website: <a href="https://seongon.com">seongon.com</a></p>
</div>
"""


def send_rejection_mail(to_email: str, to_name: str, position: str) -> tuple[bool, str]:
    """Gửi mail từ chối. Trả về (success, message_id_or_error)."""
    sender = quote(SENDER_MAIL, safe="")
    url = f"{LARK_DOMAIN}/open-apis/mail/v1/user_mailboxes/{sender}/messages/send"
    subject = f"[SEONGON] Phản hồi kết quả ứng tuyển vị trí {position}"
    body_html = _build_rejection_html(to_name, position)
    payload = {
        "subject": subject,
        "to": [{"mail_address": to_email, "name": to_name or to_email}],
        "body_html": body_html,
        "head_from": {"mail_address": SENDER_MAIL, "name": "Phòng Tuyển dụng SEONGON"},
    }

    last_err = "Không có Lark token hợp lệ"
    for token_label, token in (("user", _get_user_token()), ("tenant", _get_tenant_token())):
        if not token:
            continue
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload, timeout=20,
        ).json()
        if resp.get("code") == 0:
            msg_id = resp.get("data", {}).get("message_id", "")
            log.info("📨 Rejection mail [%s_token] sent → %s (msg_id=%s)",
                     token_label, to_email, msg_id)
            return True, msg_id
        last_err = f"code={resp.get('code')} msg={resp.get('msg') or str(resp)[:200]}"
        log.warning("Rejection mail [%s_token] failed: %s", token_label, last_err)
    return False, last_err


def patch_hrm_rejection_status(candidate_id: str, ok: bool, error_msg: str = "") -> None:
    """Cập nhật trạng thái gửi rejection email lên HRM."""
    now_str = datetime.now(_VN_TZ).strftime("%d/%m/%Y %H:%M")
    payload = {
        "rejection_email_status": "sent" if ok else "failed",
        "rejection_email_sent_at": now_str,
        "rejection_email_error": "" if ok else (error_msg[:300] if error_msg else "Lỗi không rõ"),
    }
    try:
        r = requests.patch(
            f"{HRM_API_BASE}/{candidate_id}",
            headers={"X-API-Key": HRM_KEY, "Content-Type": "application/json"},
            json=payload, timeout=15,
        )
        if r.status_code >= 400:
            log.warning("PATCH HRM rejection status failed: %s %s", r.status_code, r.text[:200])
    except Exception:
        log.exception("patch_hrm_rejection_status exception")


def process_candidate(c: dict) -> bool:
    cid      = c.get(F_ID, "")
    name     = (c.get(F_NAME) or "Ứng viên").strip()
    position = (c.get(F_POSITION) or "vị trí ứng tuyển").strip()
    email    = (c.get(F_EMAIL) or "").strip()

    if not email:
        log.warning("Skip %s — không có email", name)
        if cid:
            patch_hrm_rejection_status(cid, ok=False, error_msg="Ứng viên không có email")
        return False

    ok, info = send_rejection_mail(email, name, position)
    if cid:
        patch_hrm_rejection_status(cid, ok=ok, error_msg=info if not ok else "")

    if not ok:
        return False

    send_lark_im(
        f"❌ Đã gửi email TỪ CHỐI ứng viên\n"
        f"• Ứng viên: {name}\n"
        f"• Vị trí: {position}\n"
        f"• Email: {email}\n"
        f"• Lý do: Tình trạng = Không phù hợp"
    )
    return True


def run_once() -> None:
    log.info("=== Rejection Agent: bắt đầu quét ===")
    all_cands = fetch_candidates()
    to_reject = [c for c in all_cands if is_to_reject(c)]
    log.info("HRM: %d total → %d ứng viên cần gửi mail từ chối", len(all_cands), len(to_reject))

    sent = _load_sent()
    new_sent = 0
    for c in to_reject:
        cid = c.get(F_ID)
        if not cid or cid in sent:
            continue
        name = c.get(F_NAME) or cid
        log.info("Xử lý từ chối: %s (id=%s)", name, cid)
        if process_candidate(c):
            sent.add(cid)
            new_sent += 1
        else:
            log.warning("Skip %s — gửi mail thất bại", name)
    _save_sent(sent)
    log.info("=== Xong: %d email từ chối mới đã gửi ===", new_sent)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    run_once()
