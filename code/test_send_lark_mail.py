"""
Test gửi 1 email qua Lark Mail API (đứng riêng — không import cv_processor).
Chạy: python test_send_lark_mail.py <to_email> <to_name>
"""

import base64
import logging
import os
import sys
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("test-lark-mail")

APP_ID         = os.getenv("LARK_APP_ID", "")
APP_SECRET     = os.getenv("LARK_APP_SECRET", "")
LARK_DOMAIN    = os.getenv("LARK_DOMAIN", "https://open.larksuite.com")
CV_GMAIL_USER  = os.getenv("CV_GMAIL_USER", "tuyendung@seongon.com")
REFRESH_TOKEN  = os.getenv("CV_LARK_USER_REFRESH_TOKEN", "")


def _get_app_access_token() -> str:
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=15,
    ).json()
    return r.get("app_access_token", "")


def _get_user_access_token() -> str:
    app_token = _get_app_access_token()
    if not app_token:
        print("❌ Không lấy được app_access_token")
        return ""
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/authen/v1/oidc/refresh_access_token",
        headers={"Authorization": f"Bearer {app_token}"},
        json={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        timeout=15,
    ).json()
    print(f"[refresh] code={r.get('code')} msg={r.get('msg')}")
    return r.get("data", {}).get("access_token", "")


def test_send(to_email: str, to_name: str) -> None:
    token = _get_user_access_token()
    if not token:
        print("❌ Không lấy được Lark user access token.")
        return
    print(f"✅ User access token OK (length={len(token)})")

    sender = quote(CV_GMAIL_USER, safe="")
    url = f"{LARK_DOMAIN}/open-apis/mail/v1/user_mailboxes/{sender}/messages/send"

    body_html = f"""\
<p>Chào <b>{to_name}</b>,</p>
<p>Đây là email <b>TEST</b> từ Interview Invite Agent để xác nhận
Lark Mail API hoạt động đúng.</p>
<p>Nếu Sếp nhận được email này → phần gửi mail OK.</p>
<p>Trân trọng,<br>SEONGON Tuyển Dụng Bot</p>
"""
    body_b64 = base64.b64encode(body_html.encode("utf-8")).decode()
    payload = {
        "subject": "[SEONGON TEST] Kiểm tra Lark Mail API",
        "to": [{"mail_address": to_email, "name": to_name}],
        "body_html": body_b64,
        "head_from": {"mail_address": CV_GMAIL_USER, "name": "SEONGON Tuyển Dụng"},
    }
    print(f"→ POST {url}")
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json=payload, timeout=20,
    )
    print(f"\n=== HTTP {resp.status_code} ===")
    print(resp.text[:2000])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_send_lark_mail.py <to_email> <to_name>")
        sys.exit(1)
    test_send(sys.argv[1], sys.argv[2])
