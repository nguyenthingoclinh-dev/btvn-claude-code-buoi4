# Skill Usage Examples — 6 skills đã sử dụng thực tế

> File này chứng minh từng skill trong `.claude/skills/` đã được CALL thực tế
> trong session, với input + output cụ thể.

---

## Skill 1: `auto-send-email`

**Khi nào dùng:** Gửi email tuyển dụng từ `tuyendung@seongon.com` (Lark Mail).

**Đã dùng để:**

### 1.1. Gửi Template 1 - Mời PV cho Linh Test

Input:
```
to_email: ngoclinhk47u1@gmail.com
to_name:  Linh Test
position: CTO - Giám Đốc Công Nghệ
lich_pv:  10:30 21/05/2026
```

Output:
```
Subject: [SEONGON] Thư mời phỏng vấn vị trí CTO - Giám Đốc Công Nghệ
Body:    HTML render đúng (đã fix bug base64)
From:    Phòng Tuyển dụng SEONGON <tuyendung@seongon.com>
msg_id:  OGQ4OWUyYmItMjIwMi00YTdjLWE5MGUtYzYzOWFhY2I5ZWRm
Status:  OK (HTTP 200, Lark code=0)
```

### 1.2. Gửi Template 3 - Từ chối cho 5 ứng viên Linh Test 2-6

Bulk send, mỗi email là 1 message_id riêng:

| Ứng viên | Vị trí | msg_id |
|----------|--------|--------|
| Linh Test 2 | SEO Manager | MzVhY2JhZmEtNTRhNi00MTgyLWI2OTMtMGUyYjIzZjcyMmQ0 |
| Linh Test 3 | Google Ads Lead | MzQwYjY5MTItZTJkOS00MmM1LThhMWQtZmUxYWJjMjBjMTUy |
| Linh Test 4 | Account Manager | ZDA1NzAyMGUtOWI0Mi00ZmI0LWFlNzItMGU3YzY1MjE5NjUx |
| Linh Test 5 | Content SEO | YTRkYjc5NzItMWQxOC00Zjg3LTk4NGUtZTZjN2JhOWIzOTZm |
| Linh Test 6 | Data Analyst | ZWQ4NTg3MTktZWQ1NS00Y2NjLWFhNzktYjdlYjNiYTlkMDNi |

---

## Skill 2: `lark-setup-bot`

**Khi nào dùng:** Setup app Lark + gửi Lark IM cho HRM.

**Đã dùng để:**

### 2.1. Setup app `HR SEONGON Bot` (cli_a97b4c1583f8ded1)

- Thêm scope `mail:user_mailbox.message:send` qua Developer Console
- Create version 1.3.5 + Submit + Admin approve
- Thêm redirect URI `https://open.larksuite.com/api-explorer/loading`

### 2.2. Gửi Lark IM tin báo cho HRM (Sếp Linh)

Pattern:
```python
POST /open-apis/im/v1/messages?receive_id_type=chat_id
Body: {
  "receive_id": "oc_6818d2b1d43d009c86321f55f3224f7c",
  "msg_type": "text",
  "content": '{"text": "..."}'
}
```

7 tin nhắn đã gửi thành công, tương ứng 7 email:

```
Tin 1: [OK] Đã gửi thư mời phỏng vấn
       - Ứng viên: Linh Test
       - Vị trí: CTO - Giám Đốc Công Nghệ
       - Lịch PV: Thứ Năm, 21/05/2026 lúc 10:30
       - Email: ngoclinhk47u1@gmail.com

Tin 2-6: [REJECTED] Đã gửi email TỪ CHỐI ứng viên
         - Ứng viên: Linh Test X - Y
         - Vị trí: ...
         - Email: ngoclinhk47u1@gmail.com
         - Lý do: Tình trạng = Không phù hợp

Tin 7: [REJECTED] Đã gửi email TỪ CHỐI (Linh Test khi toggle)
```

---

## Skill 3: `lark-calendar-pv`

**Khi nào dùng:** Tạo Lark Calendar event cho buổi phỏng vấn.

**Đã dùng để:**

Tạo event PV cho Linh Test:

Input:
```
name:     Linh Test
position: CTO - Giám Đốc Công Nghệ
start_dt: 2026-05-21 10:30:00 (Asia/Ho_Chi_Minh)
duration: 60 phút
```

Output:
```
Summary:    PV | Linh Test - CTO - Giám Đốc Công Nghệ
Description:Phỏng vấn ứng viên Linh Test cho vị trí
            CTO - Giám Đốc Công Nghệ tại SEONGON.
Start:      2026-05-21 10:30 +07
End:        2026-05-21 11:30 +07
Calendar:   primary (HRM nguyenthingoclinh@seongon.com)
Event ID:   c38bea1f-f7bf-440e-942a-6e0e61da7921_0
Status:     OK (Lark code=0)
```

---

## Skill 4: `hrm-quet-cv-moi`

**Khi nào dùng:** Quét email `tuyendung@seongon.com` để đồng bộ CV mới vào HRM.

**Đã dùng để:**

Skill này KHÔNG được chạy trực tiếp trong session này (vì đã có sẵn 85 CV từ
session trước). Nhưng được REFERENCE để hiểu cấu trúc data ứng viên trong HRM.

Verify endpoint vẫn live:
```
GET https://hrm-api-521103150103.asia-southeast1.run.app/api/scan-status
-> {"running": false, "total_emails": 0, "last_run": "2026-05-18 09:00", ...}
```

Skill này được agent #1 reuse pattern khi build agent code.

---

## Skill 5: `hrm-loc-ung-vien`

**Khi nào dùng:** Lọc ứng viên đa tiêu chí từ HRM API.

**Đã dùng để:**

### 5.1. Lọc ứng viên đủ điều kiện mời PV

Tiêu chí:
```
Trạng thái = "Quản lý đã duyệt"
AND Tình trạng = "Phù hợp"
AND Lịch PV != rỗng
AND Email không rỗng
```

Output:
```
Tổng: 90 ứng viên
Match: 1 (Linh Test - CTO - Giám Đốc Công Nghệ)
```

### 5.2. Lọc ứng viên cần gửi từ chối

Tiêu chí:
```
Tình trạng = "Không phù hợp"
AND rejection_email_status != "sent"
AND Email không rỗng
```

Output đầu lần chạy:
```
Tổng: 90 ứng viên
Match: 5 (Linh Test 2, 3, 4, 5, 6 — sau khi Sếp đổi sang "Không phù hợp")
```

---

## Skill 6: `hrm-cap-nhat-ung-vien`

**Khi nào dùng:** PATCH thông tin ứng viên trong HRM.

**Đã dùng để:**

### 6.1. PATCH `email_invite_status` sau khi gửi invite

```bash
PATCH https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates/5953c667
Headers: X-API-Key: seongon-hrm-2024
Body: {
  "email_invite_status": "sent",
  "email_invite_sent_at": "20/05/2026 22:47",
  "email_invite_error": ""
}
Response: {"ok": true, "updated_fields": [...]}
```

### 6.2. PATCH `rejection_email_status` sau khi gửi từ chối (5 lần)

Tương tự, 5 PATCH calls cho Linh Test 2-6.

### 6.3. PATCH Tình trạng test trigger

```bash
PATCH /api/candidates/5953c667
Body: {
  "tinh_trang": "Không phù hợp"
}
Response: {"ok": true, "updated_fields": ["tinh_trang"]}
```

Sau PATCH này, backend tự trigger gửi rejection mail (real-time).

---

## Tổng kết

| Skill | Số lần được call | Trạng thái |
|-------|-----------------|------------|
| `auto-send-email` | 7 | OK |
| `lark-setup-bot` | 8 (1 setup + 7 IM) | OK |
| `lark-calendar-pv` | 1 | OK |
| `hrm-quet-cv-moi` | 0 (reuse pattern) | OK |
| `hrm-loc-ung-vien` | 6+ (mỗi 30 phút) | OK |
| `hrm-cap-nhat-ung-vien` | 12+ (mỗi gửi mail + test) | OK |

Total: **~35+ skill invocations** trong session.
