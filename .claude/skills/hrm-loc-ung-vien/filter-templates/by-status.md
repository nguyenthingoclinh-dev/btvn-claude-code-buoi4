# Filter template — By Status (Theo trạng thái tuyển dụng)

> Load file này CHỈ KHI user yêu cầu lọc theo trạng thái. Skill `hrm-loc-ung-vien` load-on-demand.

## Field name

```python
candidate['Trạng thái']     # string, 1 trong 7 giá trị enum
candidate['Tình trạng']      # string, 1 trong 3: "", "Phù hợp", "Không phù hợp"
```

## Enum trạng thái (theo pipeline tuyển dụng SEONGON)

| Order | Trạng thái | Ý nghĩa |
|---|---|---|
| 1 | **CV mới** | Vừa vào pipeline, chưa ai xem |
| 2 | **Lọc CV** | HR đã xem qua, đang screen |
| 3 | **Phỏng vấn chuyên môn** | Manager PV về skill |
| 4 | **Bài test** | Đang làm bài test |
| 5 | **Phỏng vấn văn hóa** | HR PV về culture fit |
| 6 | **Deal lương** | Đang đàm phán offer |
| 7 | **Onboard** | Đã nhận việc |

## Enum tình trạng

- `""` (trống) — Chưa đánh giá
- `"Phù hợp"` — Pass
- `"Không phù hợp"` — Fail/Reject

## Logic filter

```python
import json
with open('/tmp/candidates.json') as f:
    cands = json.load(f)['data']

# Đơn giản
status = "Phỏng vấn chuyên môn"
matched = [c for c in cands if c.get('Trạng thái') == status]

# Multiple trạng thái (vd: "đang PV")
in_interview = ["Phỏng vấn chuyên môn", "Bài test", "Phỏng vấn văn hóa"]
matched = [c for c in cands if c.get('Trạng thái') in in_interview]

# Combine với tình trạng
matched = [c for c in cands
           if c.get('Trạng thái') == 'CV mới'
           and c.get('Tình trạng') in ['', None]]  # chưa đánh giá

# Pipeline funnel — đếm từng stage
from collections import Counter
funnel = Counter(c.get('Trạng thái', '?') for c in cands)
```

## Sort recommend

Theo điểm AI giảm dần (ưu tiên xử lý ứng viên xịn):
```python
matched.sort(key=lambda c: int(c.get('Điểm AI', '0') or 0), reverse=True)
```

## Output table

| # | Họ tên | Vị trí | **Trạng thái** | **Tình trạng** | Điểm AI | Lý do | CV |

Highlight 2 cột chính.

## Use case phổ biến

| Câu hỏi user | Trigger |
|---|---|
| "CV nào đang chờ xem?" | Trạng thái = "CV mới" |
| "Ai đang PV?" | Trạng thái in [3 stages PV] |
| "Đã onboard ai?" | Trạng thái = "Onboard" |
| "Đã loại ai?" | Tình trạng = "Không phù hợp" |
| "Sắp deal lương cho ai?" | Trạng thái = "Deal lương" |
