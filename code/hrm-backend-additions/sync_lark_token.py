"""Sync Lark refresh token từ local .env (đã được Sếp authorize gần đây)
   sang Firestore lark_tokens/tuyendung để backend Cloud Run dùng được."""

import os
import sys
import time
import requests
from pathlib import Path

# Đọc refresh token mới nhất từ Lark Bot .env
LARK_BOT_ENV = Path("/Users/Ngoclinh/Desktop/Lark Bot/.env")
if not LARK_BOT_ENV.exists():
    print(f"❌ Không tìm thấy {LARK_BOT_ENV}")
    sys.exit(1)

refresh_token = ""
app_id = ""
app_secret = ""
for line in LARK_BOT_ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("CV_LARK_USER_REFRESH_TOKEN="):
        refresh_token = line.split("=", 1)[1].strip()
    elif line.startswith("LARK_APP_ID="):
        app_id = line.split("=", 1)[1].strip()
    elif line.startswith("LARK_APP_SECRET="):
        app_secret = line.split("=", 1)[1].strip()

if not refresh_token:
    print("❌ Không tìm thấy CV_LARK_USER_REFRESH_TOKEN trong .env")
    sys.exit(1)

print(f"✅ Đọc refresh token từ Lark Bot .env (length={len(refresh_token)})")

# Refresh để lấy access_token mới + verify token còn hạn
print("→ Refresh token để verify còn hạn + lấy access_token mới...")
app_resp = requests.post(
    "https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}, timeout=15,
).json()
app_token = app_resp.get("app_access_token", "")
if not app_token:
    print(f"❌ Không lấy được app token: {app_resp}")
    sys.exit(1)

refresh_resp = requests.post(
    "https://open.larksuite.com/open-apis/authen/v1/oidc/refresh_access_token",
    headers={"Authorization": f"Bearer {app_token}"},
    json={"grant_type": "refresh_token", "refresh_token": refresh_token},
    timeout=15,
).json()
print(f"   code={refresh_resp.get('code')} msg={refresh_resp.get('msg')}")
data = refresh_resp.get("data", {})
access_token = data.get("access_token", "")
new_refresh = data.get("refresh_token", refresh_token)
expires_in = data.get("expires_in", 7200)
if not access_token:
    print(f"❌ Refresh fail: {refresh_resp}")
    sys.exit(1)

# Ghi sang Firestore
print(f"→ Ghi sang Firestore lark_tokens/tuyendung...")
sys.path.insert(0, "/Users/Ngoclinh/Desktop/hrm-system/backend")
import db as _db

_db._get_db().collection("lark_tokens").document("tuyendung").set({
    "access_token": access_token,
    "refresh_token": new_refresh,
    "expires_at": time.time() + expires_in,
    "synced_from": "local .env (Lark Bot)",
    "synced_at_iso": __import__("datetime").datetime.now().isoformat(),
})
print(f"✅ Đã sync xong. Backend Cloud Run giờ dùng được token này.")
print(f"   access_token: {access_token[:30]}...")
print(f"   refresh_token: {new_refresh[:30]}...")
print(f"   expires_in: {expires_in}s")

# Nếu refresh token đã rotate, update lại .env
if new_refresh != refresh_token:
    print(f"\n→ Refresh token đã ROTATE, update lại Lark Bot .env...")
    import re
    content = LARK_BOT_ENV.read_text(encoding="utf-8")
    content = re.sub(r"CV_LARK_USER_REFRESH_TOKEN=.*", f"CV_LARK_USER_REFRESH_TOKEN={new_refresh}", content)
    LARK_BOT_ENV.write_text(content, encoding="utf-8")
    print(f"✅ Updated {LARK_BOT_ENV}")
