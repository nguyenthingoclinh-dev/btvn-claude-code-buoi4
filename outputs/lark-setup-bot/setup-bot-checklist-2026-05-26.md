# Setup Lark Bot — Checklist completion log

**Thời gian verify:** 2026-05-26 10:20:00 ICT
**Bot:** HR SEONGON Bot
**App ID:** `cli_a97b4c1583f8ded1`
**Status:** ✅ Production-ready

---

## Skill output: Verify checklist Lark Bot đã setup đầy đủ

Skill `lark-setup-bot` là skill hướng dẫn (guide skill), chạy khi cần bootstrap bot mới hoặc audit lại setup hiện tại. Output này là báo cáo audit cho bot đang chạy.

## ✅ Checklist (theo SKILL.md)

| Bước | Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Tạo Lark App trên Developer Console | ✅ | App ID `cli_a97b4c1583f8ded1` đã tồn tại |
| 2 | Đặt tên app | ✅ | "HR SEONGON Bot" |
| 3 | Thêm scope `mail:user_mailbox.message:send` | ✅ | Verified — skill auto-send-email gọi được Lark Mail API |
| 4 | Thêm scope `im:message:send_as_bot` | ✅ | Verified — skill send-lark-hop-dong gọi được |
| 5 | Thêm scope `calendar:calendar.event:create` | ✅ | Verified — outputs/agent-run-log.txt có event đã tạo |
| 6 | Lấy APP_ID, APP_SECRET | ✅ | Đã lưu vào `code/.env` (local) + Firestore (Cloud Run) |
| 7 | OAuth user `tuyendung@seongon.com` | ✅ | Refresh token in `lark_tokens/tuyendung` Firestore doc |
| 8 | Setup auto-refresh token (TTL 2h) | ✅ | `code/refresh_lark_token.py` chạy mỗi 90 phút |
| 9 | Test gửi tin nhắn đầu tiên | ✅ | `test_send_lark_mail.py` đã pass |
| 10 | Deploy webhook (nếu nhận event Lark) | ⚠️ Not required cho use case hiện tại |

## 🧪 API endpoints đã verify hoạt động

```
✅ POST  open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal
✅ POST  open.larksuite.com/open-apis/authen/v1/refresh_access_token
✅ POST  open.larksuite.com/open-apis/im/v1/messages (Lark IM)
✅ POST  open.larksuite.com/open-apis/mail/v1/user_mailboxes/.../messages (Lark Mail)
✅ POST  open.larksuite.com/open-apis/calendar/v4/calendars/.../events
```

## 📁 Files liên quan trong repo

- `code/refresh_lark_token.py` — auto-refresh user token
- `code/lark_mail.py` — Lark Mail OpenAPI wrapper
- `code/test_send_lark_mail.py` — test script gửi 1 email
- `code/inspect_lark_base.py` — verify Lark Base schema
- `code/list_lark_tables.py` — list các Lark Base tables

## 💡 Bot này đang được dùng bởi

- Skill `auto-send-email` — gửi email tuyển dụng
- Skill `lark-calendar-pv` — tạo lịch PV
- Agent `communication-agent` — gửi Lark IM notify HRM khi có CV mới hoặc cần action

## 🎯 Bài học cho người dùng skill này

Nếu Sếp bootstrap bot Lark mới cho dự án khác (vd: bot báo cáo doanh thu), follow đúng 10 bước trên. Pre-requisite quan trọng nhất:
1. Tài khoản admin Lark Workspace
2. Quyền tạo app + grant scope
3. Mail group nếu cần Send As (case `tuyendung@seongon.com`)

---

*Skill `lark-setup-bot` — Audit checklist completed at 2026-05-26 10:20:00 ICT*
