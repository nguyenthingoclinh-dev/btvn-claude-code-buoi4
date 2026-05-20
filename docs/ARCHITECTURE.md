# Architecture — Auto Interview Invitation Pipeline

## Bird's-eye view

```
┌────────────────────────────────────────────────────────────────────┐
│ ngoclinhhrm.com/tuyen-dung/ (Cloudflare Pages)                     │
│   ┌──────────────────────────────────────────────────┐             │
│   │ Dashboard 85 ứng viên — 11 cột (NEW: "Đã gửi Email")          │
│   │ Khi ƯV đủ 3 ĐK → nút "✉️ Gửi mời PV" sáng        │             │
│   │ Khi gửi xong → ✅ + timestamp + nút "↻ Gửi lại"  │             │
│   └────────────────┬─────────────────────────────────┘             │
└────────────────────│───────────────────────────────────────────────┘
                     │ HTTPS + X-API-Key
                     ↓
┌────────────────────────────────────────────────────────────────────┐
│ hrm-api-521103150103.asia-southeast1.run.app (Cloud Run)           │
│  Flask backend (Python)                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ GET    /api/candidates                                       │  │
│  │ PATCH  /api/candidates/{id}                                  │  │
│  │ DELETE /api/candidates/{id}                                  │  │
│  │ POST   /api/candidates/{id}/send-invite-email  ← NEW         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Modules:                                                          │
│    db.py            ← Firestore + 3 NEW fields (email_invite_*)    │
│    lark_mail.py     ← NEW: Lark Mail OpenAPI sender                │
│    email_reader.py  ← Đã có (đọc CV từ mail)                       │
│    lark_chat.py     ← Đã có (gửi IM)                               │
└────────────────────┬───────────────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┐
        ↓                          ↓
┌──────────────────┐    ┌───────────────────────────────┐
│ Firestore        │    │ Lark Open Platform (cli_...)  │
│ - candidates     │    │ - /mail/v1/.../messages/send  │
│ - jobs           │    │ - /im/v1/messages             │
│ - lark_tokens    │    │ - /calendar/v4/.../events     │
└──────────────────┘    └───────────────────────────────┘
        ↑
        │ PATCH status
        │
┌────────────────────────────────────────────────────────────────────┐
│ interview_invite_agent.py (local cron, 30 phút/lần)                │
│   Step 1: GET /api/candidates (filter 3 ĐK)                        │
│   Step 2: send_lark_mail() → user_token → tuyendung@seongon.com    │
│   Step 3: send_lark_im() → tenant_token → ou_... Sếp Linh          │
│   Step 4: create_calendar_event() → user_token → primary calendar  │
│   Step 5: PATCH /api/candidates/{id} {email_invite_status: sent}   │
└────────────────────────────────────────────────────────────────────┘
```

## Phân bổ sub-agent (Claude Code orchestration)

Khi user giao task lớn, Claude Code chính phân tích và route:

| Bước | Sub-agent | Skill sử dụng |
|------|-----------|---------------|
| Đọc HRM API tìm ứng viên đủ ĐK | `recruitment-agent` | `hrm-loc-ung-vien` |
| Gửi email mời PV | `communication-agent` | `auto-send-email` |
| Báo Lark cho HRM | `communication-agent` | `lark-setup-bot` |
| Tạo Lark Calendar event | `communication-agent` | `lark-calendar-pv` |
| PATCH HRM `email_invite_status=sent` | `recruitment-agent` | `hrm-cap-nhat-ung-vien` |

## Token flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Lark App: HR SEONGON Bot (cli_a97b4c1583f8ded1)                 │
│   Scopes user_token (NEW v1.3.5):                               │
│     • mail:user_mailbox.message:send                            │
│     • mail:user_mailbox.message:readonly                        │
│     • mail:user_mailbox.message.body:read                       │
│     • calendar:calendar                                         │
└──────┬──────────────────────────────────────────────────────────┘
       │
       ↓ OAuth (HRM nguyenthingoclinh@seongon.com authorize)
       │
       ↓ access_token + refresh_token
       │
   ┌───┴────────────────────────────────────────┐
   │ Local:  .env CV_LARK_USER_REFRESH_TOKEN    │
   │ Cloud:  Firestore lark_tokens/tuyendung    │
   └───┬────────────────────────────────────────┘
       │
       │ Mỗi lần dùng → Lark rotate refresh_token mới
       │ → save lại env / Firestore (CRITICAL — single-use!)
       │
       ↓ user_access_token (2h TTL)
   ┌───────────────────────────────────────────┐
   │ POST /open-apis/mail/v1/.../messages/send │
   │   Bearer <user_token>                     │
   │   payload.body_html = plain HTML          │
   │   payload.head_from = tuyendung@seongon.com│
   └───────────────────────────────────────────┘
```

## 3 vấn đề thực tế đã xử lý trong session

1. **Refresh token expired** (code 20038) — Lark rotate refresh_token mỗi lần dùng nhưng code cũ không save lại. → Sửa: auto-save vào `.env` ngay sau khi refresh.

2. **Tenant token không gửi được mail** (code 99991663) — Lark Mail Send REQUIRE user_token (OAuth). → Sửa: chuyển sang user_token + ensure scope `mail:user_mailbox.message:send`.

3. **Email body hiển thị base64** — Lark Mail API expect plain HTML, không decode base64 (khác Gmail API). → Sửa: bỏ `base64.b64encode()` trên body_html.
