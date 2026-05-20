"""
Agent: Tự động gửi thư mời phỏng vấn khi ứng viên đủ điều kiện trong HRM dashboard.

Nguồn dữ liệu: https://ngoclinhhrm.com/tuyen-dung/  (qua HRM API)
Endpoint:      https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates

Điều kiện kích hoạt (AND):
  - Trạng thái  = "Quản lý đã duyệt"
  - Tình trạng  = "Phù hợp"
  - Lịch PV     ≠ rỗng
  - record_id   chưa có trong interview_sent.json

Hành động (theo thứ tự):
  1. Gửi email "Thư mời phỏng vấn" qua Lark Mail API (tuyendung@seongon.com)
  2. Gửi tin Lark IM cho HRM
  3. Tạo event Lark Calendar
  4. Ghi record vào interview_sent.json để tránh gửi trùng
"""

import base64
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("interview-agent")

# ─── ENV ─────────────────────────────────────────────────────────────────────
APP_ID         = os.getenv("LARK_APP_ID", "")
APP_SECRET     = os.getenv("LARK_APP_SECRET", "")
LARK_DOMAIN    = os.getenv("LARK_DOMAIN", "https://open.larksuite.com")
SENDER_MAIL    = os.getenv("CV_GMAIL_USER", "tuyendung@seongon.com")
REFRESH_TOKEN  = os.getenv("CV_LARK_USER_REFRESH_TOKEN", "")
NOTIFY_USER_ID = os.getenv("CV_NOTIFY_USER_ID", "")
NOTIFY_EMAIL   = os.getenv("CV_NOTIFY_EMAIL", "")

HRM_API_BASE = "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates"
HRM_API = HRM_API_BASE  # backward compat
HRM_KEY = "seongon-hrm-2024"

# ─── HRM field names (key trả về từ GET /api/candidates) ────────────────────
F_ID       = "ID"
F_NAME     = "Họ tên"
F_EMAIL    = "Email"
F_POSITION = "Vị trí ứng tuyển"
F_STATUS   = "Trạng thái"
F_FIT      = "Tình trạng"
F_INTERVIEW = "Lịch PV"

STATUS_READY = "Quản lý đã duyệt"
FIT_YES      = "Phù hợp"

INTERVIEW_DURATION_MIN = 60
_VN_TZ = timezone(timedelta(hours=7))
SENT_LOG = Path(__file__).parent / "interview_sent.json"


# ─── Lark token cache ────────────────────────────────────────────────────────
_tenant_token: str = ""
_user_token: str = ""


def _get_tenant_token() -> str:
    global _tenant_token
    if _tenant_token:
        return _tenant_token
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=15,
    ).json()
    _tenant_token = r.get("tenant_access_token", "")
    return _tenant_token


def _get_app_token() -> str:
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=15,
    ).json()
    return r.get("app_access_token", "")


def _save_refresh_token(new_refresh: str) -> None:
    """Ghi refresh token mới vào .env (Lark rotate token sau mỗi lần dùng)."""
    import re
    env_path = Path(__file__).parent / ".env"
    content = env_path.read_text(encoding="utf-8")
    new_line = f"CV_LARK_USER_REFRESH_TOKEN={new_refresh}"
    if "CV_LARK_USER_REFRESH_TOKEN=" in content:
        content = re.sub(r"CV_LARK_USER_REFRESH_TOKEN=.*", new_line, content)
    else:
        content += f"\n{new_line}\n"
    env_path.write_text(content, encoding="utf-8")
    global REFRESH_TOKEN
    REFRESH_TOKEN = new_refresh


def _get_user_token() -> str:
    """User access token cho Sếp Linh. Cần REFRESH_TOKEN còn hạn.
    Lark rotate refresh token sau mỗi lần refresh → phải save lại token mới."""
    global _user_token
    if _user_token:
        return _user_token
    if not REFRESH_TOKEN:
        return ""
    app_t = _get_app_token()
    if not app_t:
        return ""
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/authen/v1/oidc/refresh_access_token",
        headers={"Authorization": f"Bearer {app_t}"},
        json={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        timeout=15,
    ).json()
    if r.get("code") != 0:
        log.warning("Lark user token refresh thất bại: code=%s msg=%s", r.get("code"), r.get("msg"))
        return ""
    data = r.get("data", {})
    _user_token = data.get("access_token", "")
    new_refresh = data.get("refresh_token", "")
    if new_refresh and new_refresh != REFRESH_TOKEN:
        _save_refresh_token(new_refresh)
        log.info("Lark refresh token đã rotate, đã lưu lại .env")
    return _user_token


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _load_sent() -> set:
    if SENT_LOG.exists():
        return set(json.loads(SENT_LOG.read_text(encoding="utf-8")))
    return set()


def _save_sent(sent: set) -> None:
    SENT_LOG.write_text(json.dumps(sorted(sent), indent=2, ensure_ascii=False), encoding="utf-8")


def _parse_interview_dt(s: str) -> datetime | None:
    """Parse '10:30 21/05/2026' → datetime aware GMT+7."""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s.strip(), "%H:%M %d/%m/%Y").replace(tzinfo=_VN_TZ)
    except ValueError:
        log.warning("Không parse được Lịch PV: %r", s)
        return None


def _fmt_vn(dt: datetime) -> str:
    days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    return f"{days[dt.weekday()]}, {dt.strftime('%d/%m/%Y')} lúc {dt.strftime('%H:%M')}"


# ─── HRM API ─────────────────────────────────────────────────────────────────

def fetch_candidates() -> list[dict]:
    r = requests.get(HRM_API, headers={"X-API-Key": HRM_KEY}, timeout=20).json()
    return r.get("data") or []


def is_ready(c: dict) -> bool:
    return (
        (c.get(F_STATUS) or "").strip() == STATUS_READY
        and (c.get(F_FIT) or "").strip() == FIT_YES
        and bool((c.get(F_INTERVIEW) or "").strip())
        # Bỏ qua ứng viên đã gửi email thành công rồi
        and (c.get("Email mời PV - Trạng thái") or "") != "sent"
    )


def patch_hrm_email_status(candidate_id: str, ok: bool, error_msg: str = "") -> None:
    """Cập nhật trạng thái gửi email lên HRM (để frontend hiện đúng)."""
    now_str = datetime.now(_VN_TZ).strftime("%d/%m/%Y %H:%M")
    payload = {
        "email_invite_status": "sent" if ok else "failed",
        "email_invite_sent_at": now_str,
        "email_invite_error": "" if ok else (error_msg[:300] if error_msg else "Lỗi không rõ"),
    }
    try:
        r = requests.patch(
            f"{HRM_API_BASE}/{candidate_id}",
            headers={"X-API-Key": HRM_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if r.status_code >= 400:
            log.warning("PATCH HRM email status failed: %s %s", r.status_code, r.text[:200])
    except Exception:
        log.exception("patch_hrm_email_status exception")


# ─── Lark Mail send ──────────────────────────────────────────────────────────

def _build_email_html(name: str, position: str, interview_str: str) -> str:
    return f"""\
<div style="font-family:Arial,sans-serif;font-size:15px;color:#222;max-width:600px">
<p>Kính gửi anh/chị <b>{name}</b>,</p>

<p>SEONGON cảm ơn anh/chị đã quan tâm và ứng tuyển vị trí <b>{position}</b> tại công ty.
Sau khi xem xét hồ sơ, chúng tôi rất ấn tượng và mong muốn được trao đổi trực tiếp với anh/chị.</p>

<p><b>Thông tin buổi phỏng vấn:</b></p>
<ul>
  <li>📅 <b>Thời gian:</b> {interview_str}</li>
  <li>📍 <b>Hình thức:</b> Online hoặc tại văn phòng SEONGON (sẽ xác nhận trước buổi PV)</li>
  <li>⏱ <b>Thời lượng dự kiến:</b> 45–60 phút</li>
</ul>

<p>Anh/chị vui lòng <b>reply email này</b> để xác nhận tham gia trước <b>24 giờ</b>
trước buổi phỏng vấn. Nếu thời gian không phù hợp, xin đề xuất khung giờ thay thế.</p>

<p>Trân trọng,<br>
<b>Phòng Tuyển dụng - SEONGON</b><br>
Email: <a href="mailto:{SENDER_MAIL}">{SENDER_MAIL}</a><br>
Website: <a href="https://seongon.com">seongon.com</a></p>
</div>
"""


def send_lark_mail(to_email: str, to_name: str, subject: str, body_html: str) -> tuple[bool, str]:
    """Gửi mail. Trả về (success, message_id_hoặc_error_msg)."""
    sender = quote(SENDER_MAIL, safe="")
    url = f"{LARK_DOMAIN}/open-apis/mail/v1/user_mailboxes/{sender}/messages/send"
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
            log.info("✉️  Lark mail [%s_token] sent → %s (msg_id=%s)",
                     token_label, to_email, msg_id)
            return True, msg_id
        last_err = f"code={resp.get('code')} msg={resp.get('msg') or str(resp)[:200]}"
        log.warning("Lark mail [%s_token] failed: %s", token_label, last_err)
    return False, last_err


# ─── Lark IM notification ────────────────────────────────────────────────────

def send_lark_im(text: str) -> None:
    token = _get_tenant_token()
    if not token:
        log.warning("Không có tenant_token để gửi Lark IM")
        return
    receive_id = NOTIFY_USER_ID
    if not receive_id:
        log.warning("CV_NOTIFY_USER_ID rỗng — bỏ qua Lark IM")
        return
    id_type = "chat_id" if receive_id.startswith("oc_") else "open_id"
    url = f"{LARK_DOMAIN}/open-apis/im/v1/messages?receive_id_type={id_type}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
        timeout=15,
    ).json()
    if resp.get("code") != 0:
        log.warning("Lark IM failed: %s", str(resp)[:300])
    else:
        log.info("💬 Lark IM sent")


# ─── Lark Calendar ───────────────────────────────────────────────────────────

def create_calendar_event(candidate_name: str, position: str, start_dt: datetime) -> str | None:
    token = _get_user_token()
    if not token:
        log.warning("Không có user_token → bỏ qua Calendar event")
        return None
    start_s = int(start_dt.timestamp())
    end_s   = start_s + INTERVIEW_DURATION_MIN * 60
    payload = {
        "summary": f"PV | {candidate_name} — {position}",
        "description": f"Phỏng vấn ứng viên {candidate_name} cho vị trí {position} tại SEONGON.",
        "need_notification": True,
        "start_time": {"timestamp": str(start_s), "timezone": "Asia/Ho_Chi_Minh"},
        "end_time":   {"timestamp": str(end_s),   "timezone": "Asia/Ho_Chi_Minh"},
        "free_busy_status": "busy",
        "visibility": "default",
    }
    resp = requests.post(
        f"{LARK_DOMAIN}/open-apis/calendar/v4/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload, timeout=15,
    ).json()
    if resp.get("code") != 0:
        log.warning("Calendar create failed: %s", str(resp)[:300])
        return None
    event_id = resp.get("data", {}).get("event", {}).get("event_id")
    log.info("📅 Calendar event created: %s", event_id)
    return event_id


# ─── Main ────────────────────────────────────────────────────────────────────

def process_candidate(c: dict) -> bool:
    cid      = c.get(F_ID, "")
    name     = (c.get(F_NAME) or "Ứng viên").strip()
    position = (c.get(F_POSITION) or "vị trí ứng tuyển").strip()
    email    = (c.get(F_EMAIL) or "").strip()
    if not email:
        log.warning("Skip %s — không có email", name)
        if cid:
            patch_hrm_email_status(cid, ok=False, error_msg="Ứng viên không có email")
        return False

    pv_dt = _parse_interview_dt(c.get(F_INTERVIEW) or "")
    interview_str = _fmt_vn(pv_dt) if pv_dt else (c.get(F_INTERVIEW) or "sẽ xác nhận sau")

    subject = f"[SEONGON] Thư mời phỏng vấn vị trí {position}"
    body_html = _build_email_html(name, position, interview_str)

    ok, info = send_lark_mail(email, name, subject, body_html)
    if cid:
        patch_hrm_email_status(cid, ok=ok, error_msg=info if not ok else "")

    if not ok:
        return False

    send_lark_im(
        f"✅ Đã gửi thư mời phỏng vấn\n"
        f"• Ứng viên: {name}\n"
        f"• Vị trí: {position}\n"
        f"• Lịch PV: {interview_str}\n"
        f"• Email: {email}"
    )

    if pv_dt:
        create_calendar_event(name, position, pv_dt)
    return True


def run_once() -> None:
    log.info("=== Interview Agent: bắt đầu quét ===")
    all_cands = fetch_candidates()
    ready = [c for c in all_cands if is_ready(c)]
    log.info("HRM: %d total → %d ứng viên đủ điều kiện", len(all_cands), len(ready))

    sent = _load_sent()
    new_sent = 0
    for c in ready:
        cid = c.get(F_ID)
        if not cid or cid in sent:
            continue
        name = c.get(F_NAME) or cid
        log.info("Xử lý: %s (id=%s)", name, cid)
        if process_candidate(c):
            sent.add(cid)
            new_sent += 1
        else:
            log.warning("Skip %s — gửi mail thất bại", name)
    _save_sent(sent)
    log.info("=== Xong: %d email mới đã gửi ===", new_sent)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    run_once()
