# Filter template — By Score (Theo điểm AI)

> Load file này CHỈ KHI user yêu cầu lọc theo điểm. Skill `hrm-loc-ung-vien` load-on-demand.

## Field name

```python
candidate['Điểm AI']  # string, vd: "78". Có thể rỗng "" nếu chưa chấm.
```

## Thang điểm SEONGON

| Khoảng | Phân loại | Đề xuất |
|---|---|---|
| 90-100 | A — Outstanding | Mời PV ngay, ưu tiên cao |
| 70-89  | B — Strong fit | Mời PV |
| 45-69  | C — Cân nhắc | Phone screen 15p |
| 25-44  | D — Yếu | Loại lịch sự |
| 0-24   | F — Không phù hợp | Loại, archive |

## Logic filter

```python
import json
with open('/tmp/candidates.json') as f:
    cands = json.load(f)['data']

# Lọc theo threshold
threshold = 70
matched = [c for c in cands
           if c.get('Điểm AI') and int(c['Điểm AI']) >= threshold]

# Trong khoảng
low, high = 45, 69
matched = [c for c in cands
           if c.get('Điểm AI') and low <= int(c['Điểm AI']) <= high]

# Top N điểm cao nhất
matched = sorted(
    [c for c in cands if c.get('Điểm AI')],
    key=lambda c: int(c['Điểm AI']),
    reverse=True
)[:10]
```

## Quy tắc parse

- Nếu `Điểm AI = ""` → coi là chưa chấm, exclude khỏi filter score
- Nếu `Điểm AI = "0"` → coi là đã chấm = 0
- Luôn dùng `int(c['Điểm AI'])`, không so sánh string

## Output table

| # | Họ tên | Vị trí | **Điểm AI** ⭐ | Đề xuất AI | Trạng thái | CV |

Highlight cột Điểm AI (cột chính của filter này).

## Đề xuất hành động dựa vào kết quả

- Nếu top có **N candidates ≥70**: list cụ thể "Mời PV: A, B, C..."
- Nếu **0 candidates ≥70**: đề xuất scan email lại + chấm điểm lại
- Nếu cả pipeline chỉ có 20-30% chấm điểm → đề xuất "Auto-chấm điểm" toàn bộ
