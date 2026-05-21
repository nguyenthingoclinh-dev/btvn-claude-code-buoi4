---
name: auto-send-email
description: This skill should be used when the user asks to "gửi email cho ứng viên", "gửi thư mời PV", "gửi thư cảm ơn sau PV", "gửi thư từ chối", "gửi mail trúng tuyển", "send interview invite email", or any candidate-facing recruitment email task. Sends email from tuyendung@seongon.com via Lark Mail OpenAPI using 4 SEONGON templates (mời PV / cảm ơn / từ chối / trúng tuyển). Use when communication-agent or main session needs to deliver formal recruitment email to a candidate.
---

# Skill: auto-send-email

Tự động gửi email tuyển dụng từ địa chỉ **`tuyendung@seongon.com`** (Lark Mail) tới ứng viên qua **Lark Mail OpenAPI**. Hỗ trợ 4 loại email phổ biến: mời PV, cảm ơn sau PV, từ chối, thông báo trúng tuyển.

---

## Khi nào dùng skill này

Trigger khi user yêu cầu:
- "Gửi email mời ứng viên X phỏng vấn vào ngày Y"
- "Gửi thư cảm ơn sau PV cho ứng viên X"
- "Gửi mail từ chối toàn bộ ứng viên vị trí Y"
- "Báo trúng tuyển cho ứng viên X"
- "Soạn + gửi email tuyển dụng"

**KHÔNG dùng** cho email nội bộ/báo cáo lãnh đạo — đó là email khác (`nguyenthingoclinh@seongon.com`).

---

## Pre-requisites đã có sẵn

- App Lark `HR SEONGON Bot` (App ID `cli_a97b4c1583f8ded1`) đã có scope `mail:user_mailbox.message:send` (user token)
- HRM (`nguyenthingoclinh@seongon.com`) đã authorize OAuth → refresh token lưu ở:
  - Local: `.env` file (`CV_LARK_USER_REFRESH_TOKEN`)
  - Production (Cloud Run): Firestore collection `lark_tokens` document `tuyendung`
- HRM có quyền **Send As** mailgroup `tuyendung@seongon.com` (cấu hình ở Lark Admin → Mail Groups)

---

## Quy trình thực hiện

### Bước 1 — Xác nhận thông tin với user

Trước khi gửi, LUÔN hỏi user xác nhận:
1. **Người nhận**: email ứng viên (có thể nhiều người)
2. **Loại email**: mời PV / cảm ơn / từ chối / trúng tuyển
3. **Thông tin biến**: tên ứng viên, vị trí, ngày giờ PV, link Meet, v.v.
4. **Người ký**: mặc định "Phòng Tuyển dụng - SEONGON" (KHÔNG ký tên cá nhân Sếp Linh)

### Bước 2 — Soạn email theo template (xem template ở dưới)

### Bước 3 — Show preview cho user duyệt

LUÔN preview nội dung email TRƯỚC khi gửi. Format:
```
📧 PREVIEW EMAIL
─────────────────
From:    tuyendung@seongon.com
To:      [email]
Subject: [tiêu đề]

[nội dung HTML]
─────────────────
Sếp duyệt gửi không?
```

### Bước 4 — Gửi qua Lark Mail OpenAPI

Chỉ chạy khi user xác nhận. Body HTML KHÔNG base64 encode (Lark Mail API không decode).

### Bước 5 — Báo kết quả

Sau khi gửi: báo lại `message_id` + danh sách email đã gửi thành công/thất bại. Lưu trạng thái vào HRM (`PATCH /api/candidates/{id}` với field `email_invite_status`).

---

## Code Python gửi email (Lark Mail OpenAPI)

```python
"""Gửi email tuyển dụng từ tuyendung@seongon.com qua Lark Mail OpenAPI."""
import os, requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

APP_ID         = os.getenv("LARK_APP_ID", "")
APP_SECRET     = os.getenv("LARK_APP_SECRET", "")
LARK_DOMAIN    = os.getenv("LARK_DOMAIN", "https://open.larksuite.com")
SENDER         = os.getenv("CV_GMAIL_USER", "tuyendung@seongon.com")
REFRESH_TOKEN  = os.getenv("CV_LARK_USER_REFRESH_TOKEN", "")


def _get_app_token() -> str:
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=15,
    ).json()
    return r.get("app_access_token", "")


def _get_user_token() -> str:
    """Lấy user access token (Lark rotate refresh token mỗi lần dùng — phải save)."""
    app_t = _get_app_token()
    r = requests.post(
        f"{LARK_DOMAIN}/open-apis/authen/v1/oidc/refresh_access_token",
        headers={"Authorization": f"Bearer {app_t}"},
        json={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        timeout=15,
    ).json()
    data = r.get("data", {})
    new_refresh = data.get("refresh_token", "")
    if new_refresh and new_refresh != REFRESH_TOKEN:
        # TODO: save new_refresh back to .env (Lark single-use refresh token!)
        pass
    return data.get("access_token", "")


def send_email(to: str, to_name: str, subject: str, body_html: str) -> dict:
    """Gửi 1 email. Trả về {ok, message_id, error}."""
    token = _get_user_token()
    if not token:
        return {"ok": False, "error": "Không có user token Lark"}

    sender = quote(SENDER, safe="")
    url = f"{LARK_DOMAIN}/open-apis/mail/v1/user_mailboxes/{sender}/messages/send"
    payload = {
        "subject": subject,
        "to": [{"mail_address": to, "name": to_name or to}],
        "body_html": body_html,   # PLAIN HTML, không base64
        "head_from": {"mail_address": SENDER, "name": "Phòng Tuyển dụng SEONGON"},
    }
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload, timeout=20,
    ).json()
    if resp.get("code") != 0:
        return {"ok": False, "error": f"code={resp.get('code')} msg={resp.get('msg')}"}
    return {"ok": True, "message_id": resp.get("data", {}).get("message_id", "")}
```

---

## 4 Template email chuẩn SEONGON

### Template 1 — Mời phỏng vấn

**Subject:** `[SEONGON] Thư mời phỏng vấn vị trí {VỊ_TRÍ}`

```html
<p>Kính gửi anh/chị <b>{TÊN_ỨNG_VIÊN}</b>,</p>
<p>SEONGON cảm ơn anh/chị đã quan tâm và ứng tuyển vị trí <b>{VỊ_TRÍ}</b>.
Sau khi xem xét hồ sơ, chúng tôi mong muốn được trao đổi trực tiếp.</p>
<p><b>Thông tin buổi phỏng vấn:</b></p>
<ul>
  <li>📅 <b>Thời gian:</b> {GIỜ}, ngày {NGÀY}</li>
  <li>📍 <b>Hình thức:</b> {ONLINE/OFFLINE} — {ĐỊA_ĐIỂM_HOẶC_LINK}</li>
  <li>⏱ <b>Thời lượng dự kiến:</b> 45–60 phút</li>
</ul>
<p>Anh/chị vui lòng reply email để xác nhận.</p>
<p>Trân trọng,<br><b>Phòng Tuyển dụng - SEONGON</b><br>
Email: tuyendung@seongon.com</p>
```

### Template 2 — Cảm ơn sau phỏng vấn

**Subject:** `[SEONGON] Cảm ơn anh/chị đã tham gia phỏng vấn vị trí {VỊ_TRÍ}`

Nội dung chính: cảm ơn đã tham gia, sẽ phản hồi kết quả trong 5–7 ngày làm việc.

### Template 3 — Từ chối ứng viên

**Subject:** `[SEONGON] Phản hồi kết quả ứng tuyển vị trí {VỊ_TRÍ}`

Nội dung chính: cảm ơn, "chưa thực sự phù hợp", sẽ lưu hồ sơ.

### Template 4 — Thông báo trúng tuyển

**Subject:** `[SEONGON] Thư mời nhận việc - Vị trí {VỊ_TRÍ}`

Nội dung chính: 🎉 thông báo trúng tuyển + ngày bắt đầu + địa điểm + lương + người liên hệ.

---

## Quy tắc bắt buộc

1. **LUÔN preview trước khi gửi.** Không tự ý gửi khi user chưa duyệt.
2. **Sender = `tuyendung@seongon.com`** — không đổi.
3. **Ký tên = "Phòng Tuyển dụng - SEONGON"** — không ký cá nhân.
4. **Subject bắt đầu `[SEONGON]`**.
5. **Body HTML plain**, KHÔNG base64 encode.
6. **Refresh token rotate** sau mỗi lần — save lại.
7. **Gửi hàng loạt:** for loop từng email, KHÔNG gom To (tránh lộ list).
8. **Lỗi 20043:** scope mail chưa cấp → Developer Console → Add scope → Create Version & Publish.
9. **Lỗi 99991663:** dùng tenant token → đổi sang user token.
10. **Lỗi 20038:** refresh token hết hạn → re-OAuth.

---

## Debug

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `code=20043` | App chưa có scope `mail:user_mailbox.message:send` | Developer Console → Permissions & Scopes → Add → Publish version |
| `code=99991663` | Dùng tenant token | Lark Mail Send REQUIRE user token (OAuth) |
| `code=20038` | Refresh token expired/đã rotate | Re-OAuth qua browser, exchange code mới |
| Body hiển thị base64 (PGRpdiBz...) | Đã base64 encode body | Gửi HTML plain, không base64 |
| `code=20029` | Redirect URI không khớp | Add URI vào Developer Console → Security Settings |
| Email vào spam | Subject quảng cáo | Subject ngắn, có `[SEONGON]` prefix |
