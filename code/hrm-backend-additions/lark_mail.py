"""Gửi email mời phỏng vấn từ tuyendung@seongon.com qua Lark Mail API.
   Reuse user token logic từ email_reader (lưu trong Firestore lark_tokens/tuyendung).
"""
import logging
import os
from datetime import datetime
from urllib.parse import quote

import requests

import email_reader  # reuse _get_user_token + token rotation

log = logging.getLogger("hrm.lark_mail")

LARK_DOMAIN = os.environ.get("LARK_DOMAIN", "https://open.larksuite.com")
SENDER_MAIL = os.environ.get("LARK_MAILBOX_USER", "tuyendung@seongon.com")
INTERVIEW_DURATION_MIN = 60


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


def _fmt_vn(lich_pv_raw: str) -> str:
    """'10:30 21/05/2026' (string HRM) → 'Thứ N, DD/MM/YYYY lúc HH:MM'."""
    if not lich_pv_raw:
        return "sẽ được xác nhận riêng"
    try:
        dt = datetime.strptime(lich_pv_raw.strip(), "%H:%M %d/%m/%Y")
        days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        return f"{days[dt.weekday()]}, {dt.strftime('%d/%m/%Y')} lúc {dt.strftime('%H:%M')}"
    except Exception:
        return lich_pv_raw


def send_invite_email(candidate: dict) -> tuple[bool, str]:
    """Gửi email mời phỏng vấn cho ứng viên. Trả về (success, message_or_error)."""
    name     = (candidate.get("Họ tên") or "Ứng viên").strip()
    position = (candidate.get("Vị trí ứng tuyển") or "vị trí ứng tuyển").strip()
    to_email = (candidate.get("Email") or "").strip()
    lich_pv  = (candidate.get("Lịch PV") or "").strip()

    if not to_email:
        return False, "Ứng viên không có email"

    user_token = email_reader._get_user_token()
    if not user_token:
        return False, "Lark Mail chưa được authorize. Liên hệ admin để authorize lại OAuth."

    body_html = _build_email_html(name, position, _fmt_vn(lich_pv))
    subject = f"[SEONGON] Thư mời phỏng vấn vị trí {position}"

    sender = quote(SENDER_MAIL, safe="")
    url = f"{LARK_DOMAIN}/open-apis/mail/v1/user_mailboxes/{sender}/messages/send"
    payload = {
        "subject": subject,
        "to": [{"mail_address": to_email, "name": name}],
        "body_html": body_html,
        "head_from": {"mail_address": SENDER_MAIL, "name": "Phòng Tuyển dụng SEONGON"},
    }
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20).json()
    except Exception as e:
        log.exception("send_invite_email exception")
        return False, f"Network error: {e}"

    if resp.get("code") != 0:
        err = resp.get("msg") or str(resp)[:200]
        log.warning("Lark mail send failed: %s", err)
        return False, f"Lark API code={resp.get('code')}: {err}"

    msg_id = resp.get("data", {}).get("message_id", "")
    log.info("Lark mail sent → %s (msg_id=%s)", to_email, msg_id)
    return True, msg_id
