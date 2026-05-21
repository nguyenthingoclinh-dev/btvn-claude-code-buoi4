---
name: lark-setup-bot
description: This skill should be used when the user asks to "tạo bot Lark", "setup app Lark", "gửi tin Lark IM", "gửi card Lark", "báo Lark cho HRM", "notify Lark", or any Lark Bot creation/messaging task. Walks through creating Lark app on Developer Console, granting scopes, connecting webhook, obtaining tenant_access_token, and sending Lark IM text/card to HRM. Use when bootstrapping a new Lark Bot or sending IM notifications from one.
---

# Skill: lark-setup-bot

Hướng dẫn tạo Lark Bot từ đầu — từ tạo app trên Lark Developer Console đến kết nối webhook, lấy token, và chạy bot Python đầu tiên.

---

## Khi nào dùng skill này

Trigger khi user hỏi hoặc yêu cầu:
- "Tạo bot Lark"
- "Setup Lark Bot"
- "Kết nối webhook Lark"
- "Lấy APP_ID, APP_SECRET Lark"
- "Bot Lark không nhận được tin nhắn"
- Bất kỳ yêu cầu liên quan đến tạo/cấu hình Lark Bot từ đầu

---

## Mục tiêu khi thực hiện skill

Sau khi chạy skill này, user sẽ có:
1. Lark App được tạo trên Developer Console với đúng quyền
2. File `.env` đầy đủ credentials
3. Bot Python đang chạy và nhận được tin nhắn từ Lark

---

## Các bước thực hiện

### BƯỚC 1 — Tạo Lark App

1. Vào https://open.larksuite.com/app (hoặc https://open.feishu.cn/app nếu dùng Feishu)
2. Click **Create App** → chọn **Custom App**
3. Điền:
   - App Name: tên bot (vd: `SEONGON HR Bot`)
   - Description: mô tả ngắn
4. Click **Create** → vào trang App vừa tạo
5. Vào **Credentials & Basic Info** → copy:
   - `App ID` → điền vào `LARK_APP_ID` trong `.env`
   - `App Secret` → điền vào `LARK_APP_SECRET` trong `.env`

---

### BƯỚC 2 — Bật quyền (Permissions)

Vào tab **Permission & Scopes** → tìm và bật các quyền sau:

**Quyền tối thiểu cho bot chat:**
- `im:message` — đọc tin nhắn gửi đến bot
- `im:message:send_as_bot` — bot gửi tin nhắn

**Quyền mở rộng (nếu cần):**
- `contact:user.id:readonly` — tra open_id theo email
- `bitable:app` — đọc/ghi Lark Base
- `calendar:calendar.event:create` — tạo lịch
- `calendar:calendar.event:read` — đọc lịch

Sau khi chọn xong → click **Publish** hoặc **Request Approval** (tùy cấu hình workspace).

---

### BƯỚC 3 — Cấu hình Event Subscription (Webhook)

Vào tab **Event Subscriptions**:

1. Bật **Enable Events**
2. Điền **Request URL**: URL webhook của bot (vd: `https://your-domain.com/webhook`)
   - Nếu đang test local: dùng ngrok — `ngrok http 3000` → lấy URL HTTPS
3. Copy **Verification Token** → điền vào `LARK_VERIFICATION_TOKEN` trong `.env`
4. Copy **Encrypt Key** (nếu bật Encrypt) → điền vào `LARK_ENCRYPT_KEY` trong `.env`
5. Click **Add Event** → chọn:
   - `im.message.receive_v1` — nhận tin nhắn mới (bắt buộc)
   - `im.message.message_read_v1` — xác nhận đã đọc (tùy chọn)

---

### BƯỚC 4 — Thêm Bot vào Group Chat (nếu cần)

Vào tab **App Features** → **Bot** → bật **Enable Bot**

Để bot có thể chat trong group:
- Vào Lark → mở group → **Settings** → **Bots** → **Add Bot** → tìm tên app vừa tạo

---

### BƯỚC 5 — Chuẩn bị code Python

**Cấu trúc tối thiểu:**

```
project/
├── .env              ← credentials
├── config.py         ← đọc env vars
├── lark_client.py    ← wrapper gọi Lark API
├── app.py            ← Flask webhook handler
└── requirements.txt
```

**requirements.txt:**
```
flask
requests
python-dotenv
pycryptodome
```

**config.py:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("LARK_APP_ID", "")
APP_SECRET = os.getenv("LARK_APP_SECRET", "")
VERIFICATION_TOKEN = os.getenv("LARK_VERIFICATION_TOKEN", "")
ENCRYPT_KEY = os.getenv("LARK_ENCRYPT_KEY", "")
LARK_DOMAIN = os.getenv("LARK_DOMAIN", "https://open.larksuite.com")
PORT = int(os.getenv("PORT", "3000"))
```

**lark_client.py** (phần core — xác thực + gửi tin nhắn):
```python
import time, json, requests
from config import APP_ID, APP_SECRET, LARK_DOMAIN

class LarkClient:
    def __init__(self):
        self._token = ""
        self._token_expire_at = 0.0

    def _tenant_access_token(self):
        if self._token and time.time() < self._token_expire_at - 60:
            return self._token
        url = f"{LARK_DOMAIN}/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10).json()
        if resp.get("code") != 0:
            raise RuntimeError(f"Lấy token thất bại: {resp}")
        self._token = resp["tenant_access_token"]
        self._token_expire_at = time.time() + int(resp.get("expire", 7200))
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._tenant_access_token()}", "Content-Type": "application/json"}

    def send_text(self, receive_id: str, text: str):
        id_type = "chat_id" if receive_id.startswith("oc_") else "open_id"
        url = f"{LARK_DOMAIN}/open-apis/im/v1/messages?receive_id_type={id_type}"
        payload = {"receive_id": receive_id, "msg_type": "text", "content": json.dumps({"text": text})}
        return requests.post(url, headers=self._headers(), json=payload, timeout=10).json()

    def reply_text(self, message_id: str, text: str):
        url = f"{LARK_DOMAIN}/open-apis/im/v1/messages/{message_id}/reply"
        payload = {"msg_type": "text", "content": json.dumps({"text": text})}
        return requests.post(url, headers=self._headers(), json=payload, timeout=10).json()

lark = LarkClient()
```

**app.py** (webhook handler cơ bản):
```python
import json, base64, hashlib
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from config import VERIFICATION_TOKEN, ENCRYPT_KEY, PORT
from lark_client import lark

app = Flask(__name__)
_seen = set()

def _decrypt(encrypt: str) -> dict:
    key = hashlib.sha256(ENCRYPT_KEY.encode()).digest()
    raw = base64.b64decode(encrypt)
    iv, ct = raw[:16], raw[16:]
    pt = AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
    return json.loads(pt[:-pt[-1]].decode())

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json(force=True)

    # Lark gửi challenge khi setup webhook
    if "challenge" in body:
        return jsonify({"challenge": body["challenge"]})

    # Giải mã nếu có encrypt
    if "encrypt" in body:
        body = _decrypt(body["encrypt"])

    # Lọc duplicate events
    event_id = body.get("header", {}).get("event_id")
    if event_id in _seen:
        return jsonify({"ok": True})
    _seen.add(event_id)

    # Xử lý tin nhắn
    event = body.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})

    if sender.get("sender_type") == "app":
        return jsonify({"ok": True})

    content = json.loads(message.get("content", "{}"))
    text = content.get("text", "").replace("@_user_1", "").strip()
    message_id = message.get("message_id")

    if text and message_id:
        lark.reply_text(message_id, f"Bot nhận được: {text}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
```

---

### BƯỚC 6 — Chạy và test

**Cài dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Chạy local + expose webhook:**
```bash
# Terminal 1 — chạy bot
python app.py

# Terminal 2 — expose ra internet
ngrok http 3000
```

Copy URL ngrok (dạng `https://xxxx.ngrok.io`) → dán vào **Request URL** trên Lark Developer Console → click **Verify**.

**Test:** Nhắn tin cho bot → bot phải reply lại.

---

### BƯỚC 7 — Deploy lên server (production)

**Option A — Google Cloud Run (khuyến nghị, ~$0-1/tháng):**
```bash
gcloud run deploy lark-bot --source . --region asia-southeast1 --allow-unauthenticated
```
→ Copy URL Cloud Run → cập nhật Request URL trên Lark Developer Console.

**Option B — Chạy background trên máy:**
```bash
nohup python app.py > bot.log 2>&1 &
```
(Cần giữ máy bật + dùng ngrok tunnel cố định)

---

## File .env mẫu

```env
LARK_APP_ID=cli_xxxxxx
LARK_APP_SECRET=xxxxxxxx
LARK_VERIFICATION_TOKEN=xxxxxxxx
LARK_ENCRYPT_KEY=xxxxxxxx
LARK_DOMAIN=https://open.larksuite.com
PORT=3000
```

> **Lưu ý:** Thêm `.env` vào `.gitignore` để không bị commit credentials lên GitHub.

---

## Debug thường gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `tenant_access_token failed` | Sai APP_ID hoặc APP_SECRET | Kiểm tra lại trong Lark Developer Console |
| Webhook trả 401 | VERIFICATION_TOKEN sai | Copy lại từ tab Event Subscriptions |
| Bot không nhận tin nhắn | Chưa bật event `im.message.receive_v1` | Vào Event Subscriptions → Add Event |
| Bot không chat được trong group | Chưa bật Bot feature hoặc chưa add bot vào group | Vào App Features → Bot → Enable |
| Lark gửi challenge nhưng webhook báo lỗi | Code chưa xử lý `challenge` | Thêm handler challenge vào đầu webhook |

---

## Lưu ý quan trọng

- Lark có 2 domain: `larksuite.com` (quốc tế) và `feishu.cn` (Trung Quốc). SEONGON dùng `larksuite.com`.
- Token `tenant_access_token` hết hạn sau 2 giờ — `LarkClient` tự làm mới, không cần lo.
- Mỗi event Lark có thể gửi **nhiều lần** (retry) — cần lọc duplicate bằng `event_id`.
- Khi deploy production, thay ngrok bằng URL cố định (Cloud Run, VPS, v.v.) rồi update lại Request URL trên Lark Console.
