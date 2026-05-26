# HRM API — Field Reference

> Load file này CHỈ KHI gặp lỗi field name hoặc cần xem full schema. Không load mặc định.

## Endpoint chính

```
GET https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates
Header: X-API-Key: ${HRM_API_KEY}
```

Response schema:
```json
{
  "data": [ /* array of candidates */ ],
  "total": 94
}
```

## Schema của 1 candidate (display keys — tên tiếng Việt có dấu)

| Field | Type | Mô tả |
|---|---|---|
| `ID` | string | Doc ID Firestore (8 ký tự) |
| `Họ tên` | string | Họ tên đầy đủ |
| `Email` | string | Email liên hệ |
| `SĐT` | string | Số điện thoại |
| `Vị trí ứng tuyển` | string | Tên vị trí (đã smart-match với 9 jobs) |
| `Năm KN` | string | Số năm kinh nghiệm |
| `Trường ĐH` | string | Trường tốt nghiệp |
| `Kỹ năng` | string | List kỹ năng, phân cách bằng dấu phẩy |
| `Tóm tắt CV` | string | 2-3 câu AI tóm tắt |
| `Link CV` | string | Signed URL GCS để xem PDF (valid 7 ngày) |
| `Nguồn` | string | "Email trực tiếp" / "TopCV" / "JobsGO" / ... |
| `Email từ` | string | Email người gửi |
| `Ngày nhận` | string | "DD/MM/YYYY HH:MM" |
| `Trạng thái` | string | 1 trong 7 stages (xem `by-status.md`) |
| `Tình trạng` | string | "" / "Phù hợp" / "Không phù hợp" |
| `Lý do` | string | Lý do phù hợp/không phù hợp (HR điền tay) |
| `Bài test` | string | URL bài test (nếu có) |
| `Link phỏng vấn` | string | URL file đánh giá PV |
| `Job ID` | string | Doc ID của job khớp |
| `Điểm AI` | string | "0"-"100" hoặc "" (chưa chấm) |
| `Điểm mạnh` | string | List điểm mạnh, ngăn cách dấu phẩy |
| `Điểm yếu` | string | List điểm yếu |
| `Đề xuất AI` | string | "Mời phỏng vấn" / "Cân nhắc" / "Không phù hợp" |
| `Ghi chú AI` | string | Nhận xét 2-3 câu cho HR |
| `Email ID` | string | Lark message_id để dedup |

## Quy tắc parse

1. **Tất cả field là string** — không có int/bool. Cần `int(c['Điểm AI'] or 0)` để so sánh số.
2. **Empty string ≠ None** — dùng `c.get('X', '') or ''` để safe.
3. **Tên field tiếng Việt có dấu** — KHÔNG đổi accent (vd `'Họ tên'`, không phải `'Ho ten'`).
4. **Field nhạy cảm**: `Email`, `SĐT`, `Link CV` — không log/print full ra console nếu không cần.

## Test endpoint

```bash
curl -s "https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates" \
  -H "X-API-Key: ${HRM_API_KEY}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('Total:', d['total']); print('First:', list(d['data'][0].keys())[:8])"
```

## Common bugs khi parse

| Bug | Fix |
|---|---|
| `KeyError: 'Họ tên'` | Dùng `.get()` không index trực tiếp |
| `TypeError: '<' not supported` | Nhớ `int()` trước khi so sánh điểm |
| `AttributeError: 'NoneType' has no...` | `(value or '')` để fallback empty string |
| Encoding lỗi tiếng Việt | Mở file với `encoding='utf-8'` |
