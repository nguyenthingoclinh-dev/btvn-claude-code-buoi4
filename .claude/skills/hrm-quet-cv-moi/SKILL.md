---
name: hrm-quet-cv-moi
description: This skill should be used when the user asks to "quét email tuyển dụng", "cập nhật CV mới", "đồng bộ HRM", "scan email N giờ qua", "fetch new CVs from email", or any sync between tuyendung@seongon.com inbox and the HRM dashboard. Triggers POST /api/scan-emails?hours=N then polls /api/scan-status until done. Use when user wants the latest applications to appear on ngoclinhhrm.com/tuyen-dung.
---

# Skill: Quét CV mới vào HRM SEONGON

Skill này tự động hoá việc cập nhật dashboard HRM tại **https://ngoclinhhrm.com/tuyen-dung/** — quét email `tuyendung@seongon.com`, xử lý CV mới bằng AI, lưu vào hệ thống.

## Khi nào dùng skill này

Trigger khi user:
- "Quét email tuyển dụng giúp tôi"
- "Cập nhật CV mới về dashboard"
- "Scan email N giờ qua"
- "Đồng bộ HRM"
- "Có CV nào mới không?"

## 🌐 Endpoint HRM API

| Endpoint | Method | Mục đích |
|---|---|---|
| `/api/scan-emails?hours=N` | POST | Trigger scan, chạy nền |
| `/api/scan-status` | GET | Poll tiến độ scan |
| `/api/candidates` | GET | Lấy danh sách ứng viên (để tổng kết) |

**Base URL:** `https://hrm-api-521103150103.asia-southeast1.run.app`
**Header:** `X-API-Key: ${HRM_API_KEY}`

## 📋 Quy trình 5 bước

### Bước 1 — Xác định khoảng thời gian quét

Hỏi user (nếu chưa rõ): "Quét email trong bao nhiêu giờ qua?"

Mapping mặc định:
- "hôm nay" → 24
- "tuần này" → 168
- "tháng này" → 720
- Không nói → 72 (3 ngày)

### Bước 2 — Trigger scan

```bash
HOURS=72  # thay theo input user
curl -s -X POST "https://hrm-api-521103150103.asia-southeast1.run.app/api/scan-emails?hours=${HOURS}" \
  -H "X-API-Key: ${HRM_API_KEY}"
```

Kết quả mong đợi: `{"status":"started", ...}` hoặc `{"status":"already_running", ...}`

### Bước 3 — Poll status mỗi 10s

```bash
until STATUS=$(curl -s "https://hrm-api-521103150103.asia-southeast1.run.app/api/scan-status" \
  -H "X-API-Key: ${HRM_API_KEY}") && echo "$STATUS" | grep -q "finished_at" && \
  ! echo "$STATUS" | grep -q '"finished_at":null'; do
  echo "$STATUS" | python3 -c "..."  # hiển thị progress
  sleep 10
done
```

Hiển thị progress cho user: `⏳ Đang quét: {processed} mới / {total_emails} email`

### Bước 4 — Lấy ứng viên top + tổng kết

```bash
curl -s "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates" \
  -H "X-API-Key: ${HRM_API_KEY}"
```

Parse JSON, lọc:
- Candidates mới (created_at trong khoảng `hours` vừa quét)
- Top 5 điểm AI cao nhất trong nhóm mới

### Bước 5 — Xuất báo cáo Markdown

Lưu file: `outputs/hrm-quet-cv-moi-{YYYY-MM-DD-HHMM}.md`

Format:
```markdown
# Báo cáo quét CV — {ngày giờ}

**Khoảng thời gian:** {N} giờ qua
**Trạng thái:** ✅ Hoàn thành

## 📊 Số liệu
| Chỉ số | Giá trị |
| Tổng email scan | {N} |
| CV mới thêm | {N} ⭐ |
| Đã có (skip) | {N} |
| Lỗi | {N} |

## 🆕 N CV mới có điểm cao nhất
1. Tên — Vị trí — XX/100 — Đề xuất
2. ...

## ✅ Đề xuất hành động
- {Action cụ thể với top candidates}

→ Mở dashboard: https://ngoclinhhrm.com/tuyen-dung/
```

## ⚠️ Vết xe đổ thường gặp

| Lỗi | Nguyên nhân | Cách tránh |
|---|---|---|
| `already_running` | Có scan khác đang chạy | Poll status, không trigger lại — đợi xong |
| Token Lark hết hạn | User token expire sau 2h | Báo user re-OAuth tại `/auth/lark` (cần làm thủ công) |
| Scan rất lâu (>5 phút) | Nhiều email + Claude AI chậm | Đó là bình thường, không restart — kiểm tra logs |
| API trả 401 | Sai X-API-Key | Đảm bảo header `X-API-Key: ${HRM_API_KEY}` |
| Polling vô tận | Network drop | Set timeout tổng tối đa 15 phút (90 lần × 10s) |
| Báo cáo sai số liệu | Đọc nhầm field name | Field chuẩn: `total_emails`, `processed`, `skipped`, `errors` |

## ✅ Tiêu chí tự kiểm trước khi finish

- [ ] Đã trigger scan với hours đúng
- [ ] Đã poll status cho tới khi `running=false` và `finished_at != null`
- [ ] Báo cáo có 4 chỉ số chính (total, processed, skipped, errors)
- [ ] Có top 3-5 candidates mới có điểm cao
- [ ] Có ≥1 đề xuất hành động cụ thể (mời PV ai, vị trí gì)
- [ ] File output lưu đúng path `outputs/hrm-quet-cv-moi-{date-time}.md`
- [ ] Link "Mở dashboard" trỏ đúng `https://ngoclinhhrm.com/tuyen-dung/`
- [ ] Không bịa số liệu — chỉ dùng response từ API
