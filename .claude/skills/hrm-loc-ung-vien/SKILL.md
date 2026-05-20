---
name: hrm-loc-ung-vien
description: "Tìm và lọc ứng viên trong HRM SEONGON tại ngoclinhhrm.com/tuyen-dung theo nhiều tiêu chí — vị trí, điểm AI, trạng thái, nguồn, thời gian. Trigger khi user yêu cầu tìm ứng viên, lọc CV, ai phù hợp với vị trí X, top ứng viên điểm cao."
---

# Skill: Lọc ứng viên trong HRM SEONGON

Skill này giúp HR Manager nhanh chóng tìm ra ứng viên phù hợp từ dashboard HRM **https://ngoclinhhrm.com/tuyen-dung/** theo nhiều tiêu chí.

## 🎯 Khi nào dùng skill này

Trigger khi user:
- "Tìm ứng viên cho vị trí [X]"
- "Lọc CV điểm AI ≥ 70"
- "Ai đang ở giai đoạn Phỏng vấn?"
- "CV nào từ TopCV?"
- "Top 10 ứng viên đáng chú ý nhất"
- "Ứng viên Content SEO có ai phù hợp?"

## 🌐 Endpoint HRM API

**GET** `https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates`
**Header:** `X-API-Key: seongon-hrm-2024`

Response trả về toàn bộ candidates. Filter làm ở client-side (Python) để tối ưu.

## 📋 Quy trình 5 bước

### Bước 1 — Xác định loại lọc

Phân tích câu hỏi user, xác định 1 trong 4 loại lọc:

| Trigger từ user | Loại lọc | Load file |
|---|---|---|
| "vị trí", "JD", "Content SEO" | by-position | `filter-templates/by-position.md` |
| "điểm AI", "≥ 70", "top" | by-score | `filter-templates/by-score.md` |
| "trạng thái", "PV", "Onboard" | by-status | `filter-templates/by-status.md` |
| "nguồn", "TopCV", "Email" | by-source | `filter-templates/by-source.md` |

**⚠️ Quan trọng:** Chỉ load file template tương ứng với loại lọc — KHÔNG load mặc định tất cả. (Load-on-demand)

### Bước 2 — Load template phù hợp

Đọc nội dung file `filter-templates/{loại}.md` để biết:
- Field name nào trong response cần filter
- Giá trị enum hợp lệ (vd: enum trạng thái)
- Cách combine với điều kiện khác

### Bước 3 — Gọi API

```bash
curl -s "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates" \
  -H "X-API-Key: seongon-hrm-2024" > /tmp/candidates.json
```

### Bước 4 — Filter + sort

Dùng Python parse JSON, áp filter, sort:
- by-score: sort descending theo `int(c['Điểm AI'])`
- by-position: filter `c['Vị trí ứng tuyển'] == X`
- by-status: filter `c['Trạng thái'] in [...]`
- by-source: filter `c['Nguồn'] == X`

### Bước 5 — Xuất bảng Markdown

Lưu file: `outputs/hrm-loc-ung-vien-{loại}-{slug}-{YYYY-MM-DD}.md`

Format:
```markdown
# Danh sách ứng viên — {Loại lọc + giá trị}

**Tổng số match:** N
**Tiêu chí:** {detail}

## Top 20 ứng viên (sort theo {field})

| # | Họ tên | Vị trí | Điểm AI | Trạng thái | Nguồn | CV |
|---|---|---|---|---|---|---|
| 1 | Lê Hải Yến | Account Executive | 78/100 | CV mới | Email | [CV](url) |
| ... |

## 💡 Đề xuất hành động
- {1-3 đề xuất cụ thể dựa trên kết quả}

🔗 Mở dashboard: https://ngoclinhhrm.com/tuyen-dung/
```

## ⚠️ Vết xe đổ thường gặp

| Lỗi | Nguyên nhân | Cách tránh |
|---|---|---|
| Load TẤT CẢ template | Quên rule load-on-demand | Phân tích trigger trước, chỉ load 1 file template |
| Filter sai field name | Tên field tiếng Việt có dấu | Dùng đúng `c['Họ tên']`, `c['Điểm AI']` (xem refs) |
| Sort string "70" > "100" | Quên parse int | Dùng `int(c.get('Điểm AI', 0) or 0)` |
| Filter cho list quá ngắn (1-2) | Tiêu chí quá strict | Mở rộng (vd: dùng `in [position]` thay vì `==`) |
| Quên link CV | Field name `'Link CV'` | Luôn include cột CV với link sẵn dùng |
| Bịa candidates | Hallucinate khi response rỗng | Nếu list rỗng, báo rõ "Không tìm thấy ai khớp" |

## ✅ Tiêu chí tự kiểm trước khi finish

- [ ] Đã xác định đúng loại lọc và load template tương ứng
- [ ] Đã gọi API thật, không bịa data
- [ ] Bảng kết quả có ≥6 cột (Tên, Vị trí, Điểm, Trạng thái, Nguồn, CV link)
- [ ] Top 10-20 candidates, sort logic
- [ ] Có ≥1 đề xuất hành động dựa vào kết quả thật
- [ ] File output đúng path `outputs/hrm-loc-ung-vien-{loại}-{slug}-{date}.md`
- [ ] Link "Mở dashboard" trỏ `https://ngoclinhhrm.com/tuyen-dung/`
- [ ] Nếu 0 kết quả → báo rõ + đề xuất giảm tiêu chí
