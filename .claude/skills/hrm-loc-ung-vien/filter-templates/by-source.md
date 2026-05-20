# Filter template — By Source (Theo nguồn CV)

> Load file này CHỈ KHI user yêu cầu lọc theo nguồn (TopCV/JobsGO/Email...). Skill `hrm-loc-ung-vien` load-on-demand.

## Field name

```python
candidate['Nguồn']  # string
```

## Enum nguồn

Nguồn phổ biến trong HRM SEONGON (theo thứ tự volume thực tế):

| Nguồn | Mô tả |
|---|---|
| **Email trực tiếp** | Ứng viên gửi CV trực tiếp tới tuyendung@seongon.com |
| **TopCV** | Từ platform TopCV (qua webhook hoặc bookmarklet) |
| **JobsGO** | Notification từ JobsGO |
| **Ybox** | Từ Ybox |
| **Glints** | Từ Glints |
| **LinkedIn** | Từ LinkedIn |
| **JobOKO** | Từ JobOKO |
| **VietnamWorks** | Từ VietnamWorks |
| **VietCV** | Từ VietCV |
| **Khác** | Các nguồn khác |

## Logic filter

```python
import json
with open('/tmp/candidates.json') as f:
    cands = json.load(f)['data']

# Đơn nguồn
source = "TopCV"
matched = [c for c in cands if c.get('Nguồn') == source]

# Nhóm: tất cả job board (loại Email trực tiếp)
job_boards = ["TopCV", "JobsGO", "VietnamWorks", "Ybox", "Glints", "JobOKO", "LinkedIn"]
matched = [c for c in cands if c.get('Nguồn') in job_boards]

# Đếm distribution
from collections import Counter
dist = Counter(c.get('Nguồn', 'Khác') for c in cands)
```

## Sort recommend

Theo ngày nhận mới nhất (để xem CV mới về từ nguồn đó):
```python
# Đã sorted từ API rồi (newest first), không cần sort lại
```

Hoặc theo điểm AI cao nhất:
```python
matched.sort(key=lambda c: int(c.get('Điểm AI', '0') or 0), reverse=True)
```

## Output

Format 2 phần:

### Phần 1 — Bảng candidates

| # | Họ tên | Vị trí | Điểm AI | Ngày nhận | CV |

### Phần 2 — Insight nguồn

| Insight | Note |
|---|---|
| Conversion rate nguồn | % candidates ≥70 / tổng |
| Avg điểm AI từ nguồn này | Mean của Điểm AI |
| Top vị trí phổ biến từ nguồn này | Counter của Vị trí |

## Đề xuất hành động

- Nguồn có conversion rate **cao** (≥30% ≥70đ) → tăng ngân sách
- Nguồn có conversion rate **thấp** (<10% ≥70đ) → cân nhắc cắt
- Nguồn nhiều CV "Không xác định" → review quy trình import (có thể cần setup forward CV trong platform)
