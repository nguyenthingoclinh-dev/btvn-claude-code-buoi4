# Outputs — Kết quả thực tế từ session

Tất cả các output sau là kết quả thật, chạy live trên production:

| File | Mô tả |
|------|-------|
| `agent-run-log.txt` | Log chạy `interview_invite_agent.py` (1 ứng viên Linh Test gửi thành công) |
| `email-received.png` | Screenshot inbox `ngoclinhk47u1@gmail.com` nhận email từ `tuyendung@seongon.com` |
| `hrm-dashboard-da-gui-email.png` | Dashboard hiện cột "Đã gửi Email" với timestamp và nút "↻ Gửi lại" |
| `lark-im-notification.png` | Lark IM gửi vào private chat của HRM |

## Cách reproduce

```bash
cd ../code
python interview_invite_agent.py
# Sau ~3s → 3 thứ xảy ra song song:
#   1. Email vào inbox ứng viên
#   2. Lark IM cho HRM
#   3. Calendar event xuất hiện trên Lark Calendar HRM
# Dashboard reload → cột "Đã gửi Email" update real-time
```
