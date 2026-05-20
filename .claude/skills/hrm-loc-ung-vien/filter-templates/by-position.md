# Filter template — By Position (Theo vị trí ứng tuyển)

> Load file này CHỈ KHI user yêu cầu lọc theo vị trí. Skill `hrm-loc-ung-vien` load-on-demand.

## Field name trong HRM API response

```python
candidate['Vị trí ứng tuyển']  # string, vd: "Account Executive (Performance)"
```

## 9 vị trí đang tuyển tại SEONGON (enum)

Lấy từ `GET /api/jobs` hoặc dùng list cố định dưới đây:

1. CTO - Giám Đốc Công Nghệ
2. Business Development (Dịch vụ SEO)
3. Account PM SEO (Executive Project Manager SEO)
4. Chuyên Viên Kế Toán
5. Biên tập viên Content SEO
6. Kỹ thuật SEO Junior – Hà Nội
7. Account Executive (Performance)
8. Chuyên Viên Kỹ Thuật SEO Website seongon.com
9. Trợ lý vận hành thương mại điện tử (Ecom)

## Logic filter

```python
import json
with open('/tmp/candidates.json') as f:
    data = json.load(f)
cands = data['data']

# Exact match
position = "Biên tập viên Content SEO"
matched = [c for c in cands if c.get('Vị trí ứng tuyển') == position]

# Fuzzy/substring match (nếu user nói tắt vd "SEO Junior")
keyword = "seo junior"
matched = [c for c in cands if keyword in c.get('Vị trí ứng tuyển','').lower()]
```

## Sort recommend

Default: theo `Điểm AI` descending để hiện ứng viên xịn nhất ở đầu:
```python
matched.sort(key=lambda c: int(c.get('Điểm AI', '0') or 0), reverse=True)
```

## Combine với điều kiện khác

Có thể kết hợp với:
- Điểm AI ≥ N: `+ [c for c in matched if int(c.get('Điểm AI','0') or 0) >= N]`
- Trạng thái = "CV mới": `+ [c for c in matched if c['Trạng thái'] == 'CV mới']`

## Output table

| # | Họ tên | Email | Điểm AI | Trạng thái | Tình trạng | Đề xuất AI | CV |
