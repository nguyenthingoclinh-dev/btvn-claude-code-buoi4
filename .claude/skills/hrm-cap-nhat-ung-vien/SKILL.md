---
name: hrm-cap-nhat-ung-vien
description: "Cập nhật thông tin ứng viên trong HRM SEONGON tại ngoclinhhrm.com/tuyen-dung — đổi trạng thái pipeline, đánh giá phù hợp hoặc không phù hợp, gắn link bài test, gắn file đánh giá phỏng vấn, xoá ứng viên. Trigger khi user yêu cầu chuyển trạng thái, đánh dấu phù hợp, gắn link bài test, xoá ứng viên."
---

# Skill: Cập nhật ứng viên trong HRM SEONGON

Skill này cho phép user (qua chat) cập nhật trạng thái pipeline tuyển dụng mà không cần mở dashboard, đặc biệt hữu ích khi cần thao tác hàng loạt.

## 🎯 Khi nào dùng skill này

Trigger khi user:
- "Chuyển trạng thái A sang Phỏng vấn chuyên môn"
- "Đánh dấu A là Phù hợp, lý do: kinh nghiệm tốt"
- "Gắn link bài test cho B: https://..."
- "Gắn file đánh giá PV cho C: https://..."
- "Xoá ứng viên X"
- "Cập nhật trạng thái 5 ứng viên thành Lọc CV"
- "Auto-promote tất cả ≥70đ sang Lọc CV"

## 🌐 HRM API Endpoints

| Endpoint | Method | Mục đích |
|---|---|---|
| `/api/candidates` | GET | Lấy danh sách (để tìm ID theo tên) |
| `/api/candidates/{id}` | PATCH | Update fields (status, tinh_trang, ly_do, bai_test...) |
| `/api/candidates/{id}` | DELETE | Xoá candidate |
| `/api/candidates/{id}/send-lark` | POST | Gửi candidate vào Lark chat |

**Base:** `https://hrm-api-521103150103.asia-southeast1.run.app`
**Header:** `X-API-Key: seongon-hrm-2024`

## 📋 Quy trình 6 bước

### Bước 1 — Phân tích intent

Xác định loại action user muốn:

| Trigger | Action | Endpoint |
|---|---|---|
| "chuyển trạng thái", "sang stage" | Update `trang_thai` | PATCH |
| "phù hợp", "không phù hợp" | Update `tinh_trang` + `ly_do` | PATCH |
| "link test", "bài test" | Update `bai_test` | PATCH |
| "file PV", "đánh giá phỏng vấn" | Update `link_phong_van` | PATCH |
| "xoá", "loại khỏi DB" | DELETE | DELETE |
| "gửi Lark" | Send to Lark | POST send-lark |

### Bước 2 — Tìm candidate ID

Nếu user gọi tên ứng viên (không phải ID):

```bash
curl -s "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates" \
  -H "X-API-Key: seongon-hrm-2024" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
target = 'Lê Hải Yến'  # tên user gọi
matches = [c for c in d['data'] if target.lower() in (c.get('Họ tên','') or '').lower()]
if len(matches) == 1: print(matches[0]['ID'])
elif len(matches) > 1:
    for c in matches: print(f\"{c['ID']} - {c['Họ tên']} - {c['Vị trí ứng tuyển']}\")
    # Hỏi user chọn cụ thể
else: print('NOT_FOUND')
"
```

Nếu có nhiều match → hỏi user disambiguate.

### Bước 3 — Validate enum (nếu update trạng thái/tình trạng)

**Trạng thái** chỉ chấp nhận 7 giá trị:
- "CV mới", "Lọc CV", "Phỏng vấn chuyên môn", "Bài test", "Phỏng vấn văn hóa", "Deal lương", "Onboard"

**Tình trạng** chỉ chấp nhận 3 giá trị:
- "" (chưa đánh giá), "Phù hợp", "Không phù hợp"

Nếu user nói tắt (vd "PV CM") → map về giá trị enum đầy đủ.

### Bước 4 — Gọi API

PATCH 1 hoặc nhiều fields cùng lúc:
```bash
curl -X PATCH "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates/{ID}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: seongon-hrm-2024" \
  -d '{
    "trang_thai": "Phỏng vấn chuyên môn",
    "tinh_trang": "Phù hợp",
    "ly_do": "Có kinh nghiệm Account 3 năm, đã làm doanh nghiệp B2B lớn"
  }'
```

DELETE candidate:
```bash
curl -X DELETE "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates/{ID}" \
  -H "X-API-Key: seongon-hrm-2024"
```

### Bước 5 — Confirm thành công

Kiểm tra response:
- PATCH success: `{"ok": true, "updated_fields": [...]}`
- DELETE success: `{"ok": true}`
- Lỗi: status 400/404/401

### Bước 6 — Báo cáo + lưu log

Lưu log: `outputs/hrm-cap-nhat-ung-vien-{action}-{YYYY-MM-DD-HHMM}.md`

Format:
```markdown
# Update HRM — {Action}

**Thực hiện:** {ngày giờ}
**Tổng số candidates updated:** N

## Chi tiết
| # | Họ tên | ID | Trước | Sau |
| 1 | Lê Hải Yến | abc123 | CV mới | Phỏng vấn chuyên môn |
| ... |

## Kết quả
- ✅ N thành công
- ❌ N lỗi (chi tiết)

🔗 Mở dashboard: https://ngoclinhhrm.com/tuyen-dung/
```

## ⚠️ Vết xe đổ thường gặp

| Lỗi | Nguyên nhân | Cách tránh |
|---|---|---|
| Tìm nhầm ứng viên (trùng tên) | Có 2 ứng viên cùng tên | Khi >1 match → hỏi user chọn ID/email cụ thể |
| Update sai enum (vd "PV CM") | User dùng từ tắt | Map về full enum trước khi PATCH |
| DELETE không có confirm | Auto delete | **Bắt buộc** confirm với user trước khi DELETE (hành động không revert được) |
| Update ≠ với current state | Race condition | Sau update, GET lại verify đúng giá trị mới |
| Batch update timeout | Loop chậm | Dùng concurrent requests hoặc batch=10 với progress bar |
| Lỗi 404 silently | Sai ID | Catch HTTP code, raise rõ ràng |
| Quên log lại trước/sau | Không có audit trail | Bắt buộc log "Trước → Sau" trong report |

## ✅ Tiêu chí tự kiểm trước khi finish

- [ ] Đã tìm đúng candidate (verify tên + ID)
- [ ] Nếu DELETE → đã confirm với user (có "Y" rõ ràng)
- [ ] Nếu enum field → đã validate hoặc map về giá trị đúng
- [ ] PATCH/DELETE trả về `ok: true` hoặc raise lỗi rõ
- [ ] Đã GET lại sau update để verify (cho hành động quan trọng)
- [ ] Log report có cột "Trước → Sau" cho audit
- [ ] File output đúng path `outputs/hrm-cap-nhat-ung-vien-{action}-{date-time}.md`
- [ ] Link dashboard ở cuối report
- [ ] Không tự ý xoá data — chỉ làm theo lệnh user
