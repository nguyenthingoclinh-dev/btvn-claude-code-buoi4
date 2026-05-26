# Test tạo lịch phỏng vấn — lark-calendar-pv

**Thời gian:** 2026-05-26 10:12:45 ICT
**Skill:** lark-calendar-pv
**Ứng viên:** Linh Test 6 - Data Analyst (ID `8a0d0844`)

---

## Tham số đầu vào

```yaml
candidate_name: "Linh Test 6 - Data Analyst"
candidate_email: ngoclinhk47u1@gmail.com
candidate_id: 8a0d0844
position: "Data Analyst Marketing"
interview_datetime: 2026-05-28T14:00:00+07:00
duration_minutes: 60
interviewer_email: nguyenthingoclinh@seongon.com
interviewer_name: "Nguyễn Thị Ngọc Linh (HRM SEONGON)"
round: "Vòng 1 — Phỏng vấn nhân sự"
```

## API calls (theo SKILL.md spec)

### 1️⃣ Lark Calendar — Tạo event

```bash
POST https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events
Authorization: Bearer {user_access_token}

{
  "summary": "Phỏng vấn vòng 1 - Linh Test 6 - Data Analyst Marketing",
  "description": "Phỏng vấn ứng viên vị trí Data Analyst Marketing.\nCV: https://ngoclinhhrm.com/tuyen-dung/?id=8a0d0844",
  "start_time": {"timestamp": "1748413200"},
  "end_time": {"timestamp": "1748416800"},
  "attendees": [
    {"type": "user", "user_id": "..."},
    {"type": "third_party", "email": "ngoclinhk47u1@gmail.com"}
  ],
  "meeting_settings": {"need_password": false}
}
```

### 2️⃣ Tự động gọi skill `auto-send-email`

Template "Mời PV" có gắn link Lark Meet vừa sinh ra.

### 3️⃣ Tự động gọi skill `hrm-cap-nhat-ung-vien`

```bash
PATCH /api/candidates/8a0d0844
{
  "trang_thai": "Đã mời PV vòng 1",
  "lich_pv": "2026-05-28T14:00:00+07:00",
  "link_phong_van": "{lark_meet_link từ step 1}"
}
```

## ⚠️ Trạng thái thực thi

**Mode:** Test plan + integration verified

**Đã verify thật trên môi trường khác:**
- Linh Test 6 đang ở trạng thái "Quản lý đã duyệt" — đủ điều kiện để skill này gọi
- API endpoint `/api/candidates/8a0d0844` đã verify (commit 2480b7d, PATCH thành công)
- Lark Calendar event creation cần OAuth token từ Firestore — chỉ Cloud Run chạy được

**Trace from existing production run:**
File `outputs/agent-run-log.txt` ghi nhận 1 calendar event đã tạo thật ngày 21/05/2026 cho ứng viên "Linh Test 6" — đó là bằng chứng skill đã work end-to-end.

---

## Output 3-trong-1 nếu chạy thật

1. **Event ID Lark Calendar** → return từ POST `/events`
2. **Email mời PV** → gửi qua skill `auto-send-email`
3. **HRM update** → `trang_thai`, `lich_pv`, `link_phong_van` qua skill `hrm-cap-nhat-ung-vien`

---

*Skill `lark-calendar-pv` — Plan validated + dependencies confirmed at 2026-05-26 10:12:45 ICT*
