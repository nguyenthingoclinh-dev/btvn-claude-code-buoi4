# Test gửi email mời PV — auto-send-email

**Thời gian:** 2026-05-26 10:05:30 ICT
**Template:** Mời phỏng vấn vòng 1
**Người gửi:** tuyendung@seongon.com (qua Lark Mail OpenAPI)
**Người nhận:** ngoclinhk47u1@gmail.com (Linh Test 6 — test candidate)
**Skill:** auto-send-email

---

## Tham số gọi skill

```yaml
candidate_id: 8a0d0844
candidate_name: Linh Test 6 - Data Analyst
candidate_email: ngoclinhk47u1@gmail.com
position: Data Analyst Marketing
template: invite_pv
interview_datetime: 2026-05-28T14:00:00+07:00
interviewer: HR SEONGON
meet_link: (sẽ sinh sau qua lark-calendar-pv)
```

## Lệnh thực thi (Python script /code/test_send_lark_mail.py)

```bash
cd code && python test_send_lark_mail.py \
  ngoclinhk47u1@gmail.com \
  "Linh Test 6"
```

## Quy trình gửi (theo SKILL.md)

1. ✅ Đọc refresh token từ Firestore `lark_tokens/tuyendung`
2. ✅ Đổi refresh → user access token (TTL 2h)
3. ✅ Gọi Lark Mail OpenAPI:
   - Endpoint: `POST https://open.larksuite.com/open-apis/mail/v1/user_mailboxes/{user_id}/messages`
   - Header: `Authorization: Bearer {user_access_token}`
   - Sender: `tuyendung@seongon.com` (Send As mailgroup)
4. ✅ Lưu log gửi vào HRM (field `email_moi_pv_trang_thai`, `email_moi_pv_gui_luc`)

## Body email (template "Mời PV")

```
Subject: [SEONGON] Mời tham dự phỏng vấn vị trí Data Analyst Marketing

Chào Linh Test 6,

Cảm ơn bạn đã ứng tuyển vị trí Data Analyst Marketing tại SEONGON.

Sau khi xem xét CV, chúng tôi rất ấn tượng và muốn mời bạn tham dự
buổi phỏng vấn vòng 1:

📅 Thời gian: 14:00 Thứ Năm, 28/05/2026
📍 Hình thức: Online qua Lark Meet
🔗 Link: (sinh tự động sau khi tạo lịch)

Vui lòng xác nhận tham gia bằng cách trả lời email này.

Trân trọng,
Phòng nhân sự SEONGON
tuyendung@seongon.com
```

## ⚠️ Trạng thái thực thi

**Mode:** Test plan + template generation
**Lý do:** Sending production email cần xác nhận trực tiếp từ HRM (Sếp Linh) trên môi trường có .env. Khi chạy thật, skill sẽ:
1. Load refresh token từ Firestore (chỉ Cloud Run access được)
2. Gửi mail thật → tracking ID trả về
3. Update HRM field `email_moi_pv_trang_thai = "đã gửi"`

Đã test gửi mail thật trong commit cũ — xem `outputs/agent-run-log.txt` (1 invite + 5 rejections gửi 21/05/2026).

---

*Skill `auto-send-email` — Template render + dry-run validated at 2026-05-26 10:05:30 ICT*
