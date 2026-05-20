"""
Tạo refresh token Lark mới khi token cũ hết hạn (lỗi 20038).

Cách dùng:
  Bước 1: python refresh_lark_token.py
          → in URL, Sếp click → authorize → copy `code` từ URL redirect
  Bước 2: python refresh_lark_token.py <code>
          → script exchange code → in refresh_token mới → tự update .env
"""

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID      = os.getenv("LARK_APP_ID", "")
APP_SECRET  = os.getenv("LARK_APP_SECRET", "")
LARK_DOMAIN = os.getenv("LARK_DOMAIN", "https://open.larksuite.com")

# Redirect URI mặc định mà Lark hỗ trợ cho dev (loading page)
REDIRECT_URI = "https://open.larksuite.com/api-explorer/loading"

# Scopes cần thiết (tên scope chính xác theo Lark API)
SCOPES = [
    "mail:user_mailbox.message:send",        # gửi mail (NEW v1.3.5)
    "mail:user_mailbox.message:readonly",    # đọc danh sách mail
    "mail:user_mailbox.message.body:read",   # đọc body mail
    "calendar:calendar",                     # tạo event Calendar
]
SCOPE_STR = " ".join(SCOPES)


def step1_print_url() -> None:
    params = {
        "app_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE_STR,
        "state": "interview-agent",
    }
    url = f"{LARK_DOMAIN}/open-apis/authen/v1/authorize?{urlencode(params)}"
    print("=" * 78)
    print("BƯỚC 1: Mở URL sau trong browser (cần đăng nhập bằng tài khoản")
    print("        nguyenthingoclinh@seongon.com — TÀI KHOẢN CÓ QUYỀN SEND-AS")
    print("        cho mailgroup tuyendung@seongon.com)")
    print("=" * 78)
    print(url)
    print()
    print("=" * 78)
    print("BƯỚC 2: Sau khi authorize, browser sẽ redirect tới URL có dạng:")
    print("        https://open.larksuite.com/api-explorer/loading?code=XXX&state=...")
    print("        Copy phần XXX (code) và chạy:")
    print()
    print("        python refresh_lark_token.py <code>")
    print("=" * 78)


def step2_exchange(code: str) -> None:
    # 1. Lấy app_access_token
    app_resp = requests.post(
        f"{LARK_DOMAIN}/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=15,
    ).json()
    app_token = app_resp.get("app_access_token", "")
    if not app_token:
        print(f"❌ Không lấy được app_access_token: {app_resp}")
        return

    # 2. Exchange code → access_token + refresh_token
    resp = requests.post(
        f"{LARK_DOMAIN}/open-apis/authen/v1/oidc/access_token",
        headers={"Authorization": f"Bearer {app_token}"},
        json={"grant_type": "authorization_code", "code": code},
        timeout=15,
    ).json()
    print(f"[exchange] code={resp.get('code')} msg={resp.get('msg')}")
    data = resp.get("data", {})
    refresh = data.get("refresh_token", "")
    access  = data.get("access_token", "")
    if not refresh:
        print(f"❌ Không lấy được refresh_token. Full response:")
        print(resp)
        return

    print(f"\n✅ NEW refresh_token: {refresh}")
    print(f"✅ NEW access_token  (sống ~2h, không cần lưu): {access[:40]}...")

    # 3. Tự cập nhật .env
    env_path = Path(__file__).parent / ".env"
    content = env_path.read_text(encoding="utf-8")
    new_line = f"CV_LARK_USER_REFRESH_TOKEN={refresh}"
    if "CV_LARK_USER_REFRESH_TOKEN=" in content:
        content = re.sub(r"CV_LARK_USER_REFRESH_TOKEN=.*", new_line, content)
    else:
        content += f"\n{new_line}\n"
    env_path.write_text(content, encoding="utf-8")
    print(f"✅ Đã cập nhật .env: CV_LARK_USER_REFRESH_TOKEN")
    print("\nBước tiếp theo:")
    print("  python test_send_lark_mail.py ngoclinhk47u1@gmail.com 'Linh Test'")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        step2_exchange(sys.argv[1])
    else:
        step1_print_url()
