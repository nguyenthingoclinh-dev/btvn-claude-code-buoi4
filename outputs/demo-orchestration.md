# Demo Orchestration — Claude Code phân bổ 1 nhiệm vụ lớn cho 2 sub-agents

> Đây là demo cho thấy cách Claude Code chính nhận **1 nhiệm vụ lớn** từ user
> và tự phân bổ cho 2 sub-agents (`recruitment-agent` + `communication-agent`)
> sử dụng các skills thích hợp.

---

## Nhiệm vụ lớn từ user

```
Tôi muốn webapp HRM SEONGON có 2 Agent chạy đồng thời:

  Agent 1 — Tự động gửi thư mời PV khi ứng viên ở trạng thái
            "Quản lý đã duyệt" + "Phù hợp" + có Lịch PV.

  Agent 2 — Tự động gửi thư từ chối khi Tình trạng = "Không phù hợp".

Cả 2 phải báo Lark IM cho HRM sau khi gửi. Có cột "Đã gửi Email" +
nút "Gửi lại" trên dashboard. Khi đổi Tình trạng Phù hợp <-> Không
phù hợp thì gửi đúng email tương ứng (kể cả khi đã gửi lần trước).
```

---

## Bước 1 — Claude Code chính phân tích task

Task lớn này có **2 sub-task song song**:

| Sub-task | Phù hợp với sub-agent | Skills cần dùng |
|----------|----------------------|-----------------|
| A. Đọc danh sách ứng viên + filter điều kiện | `recruitment-agent` | `hrm-loc-ung-vien` |
| B. Gửi 2 loại email + Lark IM + Calendar | `communication-agent` | `auto-send-email`, `lark-setup-bot`, `lark-calendar-pv` |
| C. PATCH HRM cập nhật status sau khi gửi | `recruitment-agent` | `hrm-cap-nhat-ung-vien` |

---

## Bước 2 — Phân bổ cho `recruitment-agent`

**Trigger:** Claude Code gọi sub-agent `recruitment-agent` với prompt:

```
Sub-agent: recruitment-agent

Task: Query HRM API tại
https://hrm-api-521103150103.asia-southeast1.run.app/api/candidates
để tìm ứng viên thoả 2 nhóm điều kiện:

NHÓM 1 (cần gửi invite):
  Trạng thái = "Quản lý đã duyệt"
  AND Tình trạng = "Phù hợp"
  AND Lịch PV != rỗng
  AND email_invite_status != "sent" (chưa gửi invite)

NHÓM 2 (cần gửi rejection):
  Tình trạng = "Không phù hợp"
  AND rejection_email_status != "sent"

Trả về 2 list candidate IDs cho từng nhóm.

Sau khi communication-agent gửi mail xong:
  PATCH /api/candidates/{id} với:
    NHÓM 1 -> email_invite_status=sent, email_invite_sent_at=<now>
    NHÓM 2 -> rejection_email_status=sent, rejection_email_sent_at=<now>
```

**Skills `recruitment-agent` dùng:**
- [`hrm-loc-ung-vien`](../.claude/skills/hrm-loc-ung-vien/SKILL.md) — filter ứng viên đa tiêu chí
- [`hrm-cap-nhat-ung-vien`](../.claude/skills/hrm-cap-nhat-ung-vien/SKILL.md) — PATCH status sau khi gửi

**Output thực tế từ recruitment-agent:**

```json
{
  "nhom_1_invite": [
    {
      "id": "5953c667",
      "ho_ten": "Linh Test",
      "email": "ngoclinhk47u1@gmail.com",
      "vi_tri": "CTO - Giám Đốc Công Nghệ",
      "lich_pv": "10:30 21/05/2026"
    }
  ],
  "nhom_2_rejection": [
    {"id": "defa5795", "ho_ten": "Linh Test 2 - SEO Manager", ...},
    {"id": "1a188a6b", "ho_ten": "Linh Test 3 - Google Ads Lead", ...},
    {"id": "faa82ee3", "ho_ten": "Linh Test 4 - Account Manager", ...},
    {"id": "36b74930", "ho_ten": "Linh Test 5 - Content SEO", ...},
    {"id": "8a0d0844", "ho_ten": "Linh Test 6 - Data Analyst", ...}
  ]
}
```

---

## Bước 3 — Phân bổ cho `communication-agent`

**Trigger:** Claude Code gọi sub-agent `communication-agent` với prompt:

```
Sub-agent: communication-agent

Task: Nhận 2 list ứng viên từ recruitment-agent.

Với mỗi ứng viên NHÓM 1 (invite):
  1. Gửi email Template 1 (Mời PV) qua Lark Mail từ tuyendung@seongon.com
  2. Gửi Lark IM cho HRM báo đã gửi
  3. Tạo Lark Calendar event PV vào đúng Lịch PV

Với mỗi ứng viên NHÓM 2 (rejection):
  1. Gửi email Template 3 (Từ chối) qua Lark Mail từ tuyendung@seongon.com
  2. Gửi Lark IM cho HRM báo đã gửi

Lưu ý: body_html PLAIN HTML, KHÔNG base64 encode.
       Dùng user_access_token (OAuth của HRM), KHÔNG dùng tenant_token.
```

**Skills `communication-agent` dùng:**
- [`auto-send-email`](../.claude/skills/auto-send-email/SKILL.md) — Template 1 + Template 3
- [`lark-setup-bot`](../.claude/skills/lark-setup-bot/SKILL.md) — Lark IM tới Sếp Linh
- [`lark-calendar-pv`](../.claude/skills/lark-calendar-pv/SKILL.md) — Calendar event

**Output thực tế từ communication-agent:**

```
NHOM 1 - INVITE:
  [OK] Linh Test: email mời PV sent -> msg_id=OGQ4OWUyYmI...
       Lark IM sent -> Sếp Linh
       Calendar event created -> c38bea1f-f7bf-440e-...

NHOM 2 - REJECTION:
  [OK] Linh Test 2: rejection sent -> msg_id=MzVhY2JhZmE...
                    Lark IM sent
  [OK] Linh Test 3: rejection sent -> msg_id=MzQwYjY5MTI...
                    Lark IM sent
  [OK] Linh Test 4: rejection sent -> msg_id=ZDA1NzAyMGU...
                    Lark IM sent
  [OK] Linh Test 5: rejection sent -> msg_id=YTRkYjc5NzI...
                    Lark IM sent
  [OK] Linh Test 6: rejection sent -> msg_id=ZWQ4NTg3MTk...
                    Lark IM sent

TONG: 1 invite + 5 rejection + 6 Lark IM + 1 Calendar event
```

---

## Bước 4 — recruitment-agent PATCH status

Sau khi communication-agent confirm gửi xong, recruitment-agent loop qua từng
candidate và PATCH:

```bash
# Cho Linh Test (invite)
PATCH /api/candidates/5953c667
{
  "email_invite_status": "sent",
  "email_invite_sent_at": "20/05/2026 22:47",
  "email_invite_error": ""
}

# Cho Linh Test 2-6 (rejection)
PATCH /api/candidates/{id}
{
  "rejection_email_status": "sent",
  "rejection_email_sent_at": "21/05/2026 08:43",
  "rejection_email_error": ""
}
```

Status hiển thị real-time trên dashboard sau khi user F5.

---

## Bước 5 — Real-time trigger từ Backend (kèm Lark IM)

Để tránh phải chạy local agent mỗi 30 phút, Claude Code chính còn implement
**real-time trigger** trong backend PATCH endpoint:

```python
# backend/app.py - update_candidate route

# Snapshot BEFORE update
c_before = db.get_candidate(candidate_id) or {}
old_tinh_trang = c_before.get("Tình trạng", "")

updated = db.update_candidate_fields(candidate_id, data)

# Snapshot AFTER update
c_after = db.get_candidate(candidate_id) or {}
new_tinh_trang = c_after.get("Tình trạng", "")

# Trigger rejection nếu transition vào "Không phù hợp"
if new_tinh_trang == "Không phù hợp":
    transitioned = (old_tinh_trang != new_tinh_trang)
    if transitioned or not_yet_sent:
        Thread(target=_trigger_send_rejection,
               args=(id, transitioned)).start()
```

Background thread gọi `lark_mail.send_rejection_email()` + `send_lark_im()`.

---

## Kết quả cuối cùng

| Metric | Số liệu |
|--------|---------|
| Email mời PV gửi thành công | 1 |
| Email từ chối gửi thành công | 6 |
| Lark IM báo HRM | 7 |
| Lark Calendar event | 1 |
| Backend deployed | Cloud Run rev `hrm-api-00059-j8f` |
| Frontend deployed | Cloudflare Pages `ngoclinhhrm.com` |
| Total ứng viên trong HRM | 90 |
| Code thực tế đã viết/sửa | ~4,200 dòng |

---

## Sơ đồ phân bổ trực quan

```
            User: "Webapp HRM cần 2 Agent chạy đồng thời..."
                                |
                                v
                    +-------------------------+
                    |   Claude Code (main)    |
                    |   Phân tích nhiệm vụ    |
                    +-----------+-------------+
                                |
            +-------------------+--------------------+
            |                                        |
            v                                        v
    +-----------------+                  +----------------------+
    | recruitment-    |                  | communication-agent  |
    | agent           |                  |                      |
    +-----------------+                  +----------------------+
    | hrm-loc-ung-    |                  | auto-send-email      |
    |   vien          |                  | lark-setup-bot       |
    | hrm-cap-nhat-   |                  | lark-calendar-pv     |
    |   ung-vien      |                  |                      |
    | (hrm-quet-cv-   |                  |                      |
    |   moi - reuse)  |                  |                      |
    +-----------------+                  +----------------------+
            |                                        |
            +-------------------+--------------------+
                                |
                                v
                    +---------------------------+
                    | Output thực tế:           |
                    | - 1 invite mail           |
                    | - 6 rejection mail        |
                    | - 7 Lark IM               |
                    | - 1 Calendar event        |
                    | - Dashboard column update |
                    +---------------------------+
```
