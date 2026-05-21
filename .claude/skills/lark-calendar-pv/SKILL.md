---
name: lark-calendar-pv
description: This skill should be used when the user asks to "tạo lịch phỏng vấn", "đặt lịch PV", "book interview", "schedule interview cho ứng viên X vào ngày Y", or any Lark Calendar event for a candidate interview. Creates Lark Calendar event with Google Meet/Lark Meet link, invites interviewer + HRM, syncs back to HRM dashboard. Use when scheduling a confirmed interview slot for a candidate.
---

# Skill: lark-calendar-pv

Tạo lịch phỏng vấn ứng viên trên Lark Calendar trong 1 lệnh. Sinh event có Lark Meet link, mời đủ người, gắn HRM, gửi email mời PV cho ứng viên cùng lúc.

---

## Khi nào dùng skill này

Trigger khi user yêu cầu:
- "Tạo lịch PV cho ứng viên X vào ngày Y"
- "Book PV với ứng viên Z lúc 14h thứ 5"
- "Schedule interview SEO Manager"
- "Đặt lịch phỏng vấn vòng 2 cho 5 ứng viên"
- "Mời PV ứng viên đã qua vòng 1"

---

## Output bắt buộc

Mỗi lần chạy, skill phải sinh ra **3 thứ** cùng lúc:

1. **Event Lark Calendar** với Lark Meet link tự động
2. **Email mời PV** gửi tới ứng viên (qua skill `auto-send-email`, template "Mời phỏng vấn")
3. **Cập nhật HRM dashboard** trạng thái ứng viên → "Đã mời PV" + gắn thời gian PV (qua skill `hrm-cap-nhat-ung-vien`)

---

## Thông tin cần thu thập

Hỏi user 7 thông tin (nếu chưa đủ):

| # | Thông tin | Ví dụ | Bắt buộc |
|---|-----------|-------|----------|
| 1 | Tên ứng viên | Nguyễn Văn A | ✓ |
| 2 | Email ứng viên | a.nguyen@gmail.com | ✓ |
| 3 | Vị trí ứng tuyển | SEO Executive | ✓ |
| 4 | Vòng PV | Vòng 1 / Vòng 2 / Vòng cuối | ✓ |
| 5 | Ngày + giờ PV | 2026-05-25 14:00 | ✓ |
| 6 | Thời lượng | 60 phút (mặc định) | – |
| 7 | Hình thức + người PV | Online qua Lark Meet — Anh Tuấn (SEO Lead) | ✓ |

**Mặc định nếu không có:**
- Thời lượng: 60 phút
- Hình thức: Online (Lark Meet tự sinh)
- Người PV thứ 2: HRM Linh (luôn có mặt)

---

## Lark Calendar API — endpoint chính

**Tạo event:**
```
POST {LARK_DOMAIN}/open-apis/calendar/v4/calendars/{calendar_id}/events
```

**Lấy calendar_id của HRM Linh (chạy 1 lần, cache lại):**
```
GET /open-apis/calendar/v4/calendars/primary
```

**Body event mẫu:**
```json
{
  "summary": "[PV Vòng 1] SEONGON × Nguyễn Văn A - SEO Executive",
  "description": "Phỏng vấn vòng 1 vị trí SEO Executive.\nỨng viên: Nguyễn Văn A\nEmail: a.nguyen@gmail.com\nNgười PV: Anh Tuấn (SEO Lead) + Chị Linh (HRM)",
  "start_time": {
    "timestamp": "1748160000",
    "timezone": "Asia/Ho_Chi_Minh"
  },
  "end_time": {
    "timestamp": "1748163600",
    "timezone": "Asia/Ho_Chi_Minh"
  },
  "vchat": {
    "vc_type": "vc"
  },
  "attendee_ability": "can_see_others",
  "free_busy_status": "busy",
  "color": -1
}
```

**Thêm người tham dự (sau khi tạo event):**
```
POST /open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees
```

Body:
```json
{
  "attendees": [
    {"type": "user", "user_id": "ou_xxx"},   ← open_id HRM Linh
    {"type": "user", "user_id": "ou_yyy"},   ← open_id người PV chuyên môn
    {"type": "third_party", "third_party_email": "a.nguyen@gmail.com"}  ← email ứng viên
  ],
  "need_notification": true
}
```

---

## Permissions Lark App cần bật

Vào [open.larksuite.com](https://open.larksuite.com) → App → Permissions → bật:
- `calendar:calendar.event:create` — tạo event
- `calendar:calendar.event:read` — đọc event (để check trùng giờ)
- `calendar:calendar.event.attendee:read` — đọc attendee
- `calendar:calendar:read` — đọc calendar
- `contact:user.id:readonly` — tra open_id người PV theo email

**Nếu chưa bật**, skill phải dừng và hướng dẫn user vào console bật trước.

---

## Code Python — `lark_calendar.py`

Lưu vào `/Users/Ngoclinh/Desktop/Lark Bot/lark_calendar.py`:

```python
"""
lark-calendar-pv: Tạo lịch phỏng vấn ứng viên trên Lark Calendar.
"""
import requests
from datetime import datetime, timedelta
from typing import Any
from lark_client import lark
from config import LARK_DOMAIN


HRM_LINH_EMAIL = "nguyenthingoclinh@seongon.com"
DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"


def _to_timestamp(dt_str: str) -> str:
    """dt_str: '2026-05-25 14:00' → unix timestamp string."""
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    return str(int(dt.timestamp()))


def get_primary_calendar_id() -> str:
    """Lấy calendar_id mặc định của tenant_access_token (HRM Linh)."""
    url = f"{LARK_DOMAIN}/open-apis/calendar/v4/calendars/primary"
    resp = requests.post(url, headers=lark._headers(), timeout=10).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"Lấy primary calendar thất bại: {resp}")
    return resp["data"]["calendars"][0]["calendar"]["calendar_id"]


def create_pv_event(
    candidate_name: str,
    candidate_email: str,
    position: str,
    round_name: str,
    start_datetime: str,
    duration_minutes: int = 60,
    interviewer_email: str | None = None,
) -> dict:
    """Tạo 1 event PV trên Lark Calendar + mời các attendee."""
    calendar_id = get_primary_calendar_id()
    start_ts = _to_timestamp(start_datetime)
    end_dt = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M") + timedelta(minutes=duration_minutes)
    end_ts = str(int(end_dt.timestamp()))

    summary = f"[PV {round_name}] SEONGON × {candidate_name} - {position}"
    description = (
        f"Phỏng vấn {round_name} vị trí {position}.\n"
        f"Ứng viên: {candidate_name}\n"
        f"Email: {candidate_email}\n"
        f"Người PV: Chị Linh (HRM)"
        + (f" + {interviewer_email}" if interviewer_email else "")
    )

    # 1. Tạo event
    url = f"{LARK_DOMAIN}/open-apis/calendar/v4/calendars/{calendar_id}/events"
    body = {
        "summary": summary,
        "description": description,
        "start_time": {"timestamp": start_ts, "timezone": DEFAULT_TIMEZONE},
        "end_time": {"timestamp": end_ts, "timezone": DEFAULT_TIMEZONE},
        "vchat": {"vc_type": "vc"},   # Lark Meet tự sinh link
        "attendee_ability": "can_see_others",
        "free_busy_status": "busy",
    }
    resp = requests.post(url, headers=lark._headers(), json=body, timeout=15).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"Tạo event thất bại: {resp}")
    event = resp["data"]["event"]
    event_id = event["event_id"]
    meet_url = event.get("vchat", {}).get("meeting_url", "")

    # 2. Add attendees
    attendees = []
    # HRM Linh (luôn có)
    hrm_open_id = lark.get_open_id_by_email(HRM_LINH_EMAIL)
    if hrm_open_id:
        attendees.append({"type": "user", "user_id": hrm_open_id})
    # Người PV chuyên môn (nếu có email Lark nội bộ)
    if interviewer_email and interviewer_email.endswith("@seongon.com"):
        interviewer_open_id = lark.get_open_id_by_email(interviewer_email)
        if interviewer_open_id:
            attendees.append({"type": "user", "user_id": interviewer_open_id})
    # Ứng viên (third party email)
    attendees.append({"type": "third_party", "third_party_email": candidate_email})

    if attendees:
        att_url = f"{LARK_DOMAIN}/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees"
        att_body = {"attendees": attendees, "need_notification": True}
        att_resp = requests.post(att_url, headers=lark._headers(), json=att_body, timeout=15).json()
        if att_resp.get("code") != 0:
            print(f"⚠ Thêm attendee thất bại: {att_resp}")

    return {
        "ok": True,
        "event_id": event_id,
        "meet_url": meet_url,
        "summary": summary,
        "start": start_datetime,
        "duration_minutes": duration_minutes,
    }


def check_conflict(start_datetime: str, duration_minutes: int = 60) -> list[dict]:
    """Check xem khung giờ có trùng với event nào khác của HRM Linh không."""
    calendar_id = get_primary_calendar_id()
    start_ts = _to_timestamp(start_datetime)
    end_dt = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M") + timedelta(minutes=duration_minutes)
    end_ts = str(int(end_dt.timestamp()))
    url = f"{LARK_DOMAIN}/open-apis/calendar/v4/calendars/{calendar_id}/events"
    params = {"start_time": start_ts, "end_time": end_ts}
    resp = requests.get(url, headers=lark._headers(), params=params, timeout=10).json()
    return resp.get("data", {}).get("items", []) or []


if __name__ == "__main__":
    import json
    result = create_pv_event(
        candidate_name="Nguyễn Văn A",
        candidate_email="a.nguyen@gmail.com",
        position="SEO Executive",
        round_name="Vòng 1",
        start_datetime="2026-05-25 14:00",
        duration_minutes=60,
        interviewer_email="tuan@seongon.com",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## Quy trình thực hiện skill (cho Claude)

### Bước 1: Thu thập thông tin

Hỏi user 7 thông tin ở bảng phía trên. Nếu user chỉ nói "tạo lịch PV cho A vào 14h thứ 5", hỏi tiếp các trường còn thiếu.

### Bước 2: Check conflict

Gọi `check_conflict()` → nếu khung giờ đã có event khác, cảnh báo user và đề xuất khung giờ trống.

### Bước 3: Preview cho user duyệt

```
📅 PREVIEW LỊCH PHỎNG VẤN
─────────────────────────────
Tiêu đề:    [PV Vòng 1] SEONGON × Nguyễn Văn A - SEO Executive
Thời gian:  14:00 - 15:00, Thứ 5 ngày 25/05/2026
Hình thức:  Online (Lark Meet sẽ tự sinh link)
Tham dự:
  • Chị Linh (HRM)
  • Anh Tuấn (SEO Lead) — tuan@seongon.com
  • Nguyễn Văn A (ứng viên) — a.nguyen@gmail.com

📧 Email mời PV: sẽ gửi tới a.nguyen@gmail.com sau khi tạo lịch
🔄 HRM dashboard: sẽ update trạng thái → "Đã mời PV"
─────────────────────────────
Sếp duyệt tạo không?
```

### Bước 4: Thực thi sau khi user xác nhận

1. Chạy `create_pv_event()` → có `event_id` + `meet_url`
2. Gọi skill **`auto-send-email`** với template "Mời phỏng vấn", điền `meet_url` vào trường link
3. Gọi skill **`hrm-cap-nhat-ung-vien`** để update HRM dashboard

### Bước 5: Báo cáo kết quả

```
✅ Đã tạo lịch PV thành công
• Event ID: omn_xxx
• Lark Meet: https://vc.larksuite.com/j/xxx
• Email mời PV đã gửi tới a.nguyen@gmail.com (Message ID: 18c...)
• HRM dashboard: trạng thái = "Đã mời PV"
```

---

## Tạo lịch hàng loạt

Khi user yêu cầu "Tạo lịch PV cho 5 ứng viên đã qua vòng 1":

1. Lọc danh sách qua skill `hrm-loc-ung-vien` (trạng thái = "Qua vòng 1")
2. Hỏi user khung giờ batch (vd: 25/05 9h-12h, mỗi PV 30 phút)
3. Tự phân chia khung giờ: 9:00, 9:30, 10:00, 10:30, 11:00
4. Preview cả 5 lịch → user duyệt → chạy `create_pv_event()` 5 lần

---

## Quy tắc bắt buộc

1. **LUÔN check conflict trước khi tạo** — không tạo lịch chồng với lịch HRM Linh đã có.
2. **LUÔN preview trước khi gửi** — không tự ý tạo lịch + gửi mail khi user chưa duyệt.
3. **HRM Linh là attendee bắt buộc** trong mọi event PV — không bỏ.
4. **Tiêu đề event chuẩn:** `[PV {Vòng}] SEONGON × {Tên} - {Vị trí}`
5. **Email mời PV phải có Lark Meet link** — copy từ `meet_url` của event vừa tạo.
6. **Update HRM dashboard** sau khi tạo lịch thành công — không bỏ bước này.

---

## Debug

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `code 99991663` | Chưa bật scope `calendar:calendar.event:create` | Vào open.larksuite.com → App → Permissions → bật scope, publish lại |
| Attendee ứng viên không nhận email | Lark chỉ gửi mail invite cho `@larksuite.com` user, third-party email cần dùng `need_notification: true` | Đảm bảo body có `need_notification: true` |
| Meet URL trả về rỗng | Trường `vchat.vc_type` thiếu hoặc workspace chưa bật Lark Meet | Check workspace, hoặc đổi sang Google Meet (gắn link manual) |
| Trùng giờ với event khác | Có | Hỏi user khung giờ khác, hoặc gợi ý khung trống gần nhất |
| Open_id của người PV nội bộ trả None | Email người PV không match Lark | Check email công ty đúng định dạng `@seongon.com` |

---

## Liên kết với các skill khác

- **`hrm-loc-ung-vien`** — Lọc danh sách ứng viên cần mời PV (input cho batch tạo lịch)
- **`auto-send-email`** — Gửi email mời PV cho ứng viên (template "Mời phỏng vấn" đã có sẵn)
- **`hrm-cap-nhat-ung-vien`** — Update trạng thái ứng viên sau khi tạo lịch
- **`lark-setup-bot`** — Đảm bảo Lark App đã được tạo + bật scope Calendar
