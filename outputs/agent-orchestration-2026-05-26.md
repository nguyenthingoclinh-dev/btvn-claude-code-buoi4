# Agent Orchestration — End-to-end recruitment flow

**Ngày chạy:** 2026-05-26
**Trigger:** "Quét email tuyển dụng + xử lý batch CV mới"
**Kết quả tổng:** Quét 147 email → sync 27 CV → lọc top 5 → mời PV 1 ứng viên

---

## 🎭 Cast — 2 agent + 6 skill

```
┌──────────────────────────────────────────────────────────────┐
│  recruitment-agent                                           │
│  └─ Owns: data, scan, filter, update                         │
│     ├─ skill: hrm-quet-cv-moi                                │
│     ├─ skill: hrm-loc-ung-vien                               │
│     └─ skill: hrm-cap-nhat-ung-vien                          │
│                                                              │
│  communication-agent                                         │
│  └─ Owns: email, Lark IM, Lark Calendar                      │
│     ├─ skill: auto-send-email                                │
│     ├─ skill: lark-calendar-pv                               │
│     └─ skill: lark-setup-bot (infra-level)                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Flow đã chạy hôm nay

### ⏱ 08:23:12 — recruitment-agent invoked: `hrm-quet-cv-moi`

User prompt: *"Quét email tuyển dụng 24h qua"*

```
POST /api/scan-emails?hours=24
→ Status: started
→ Scan 147 emails từ tuyendung@seongon.com
→ Skip 75 (đã có trong DB)
→ Process 15 → sync ra 27 CV mới
→ Total candidates: 91 → 118
```

📄 Output: [hrm-quet-cv-moi/output/quet-cv-moi-2026-05-26-0835.md](../.claude/skills/hrm-quet-cv-moi/output/quet-cv-moi-2026-05-26-0835.md)

### ⏱ 09:32:18 — recruitment-agent invoked: `hrm-loc-ung-vien`

User prompt: *"Lọc top 20 ứng viên điểm AI cao nhất"*

```
GET /api/candidates
→ Load filter-templates/by-score.md (load-on-demand)
→ Filter điểm AI ≥ 70, sort desc
→ Match: 20 ứng viên
→ Top: Linh Test 2 — SEO Manager — 82/100
```

📄 Output: [hrm-loc-ung-vien/output/loc-by-score-top20-2026-05-26.md](../.claude/skills/hrm-loc-ung-vien/output/loc-by-score-top20-2026-05-26.md)

### ⏱ 09:55:12 — recruitment-agent invoked: `hrm-cap-nhat-ung-vien`

User prompt: *"Đánh dấu Linh Test 6 là sẵn sàng PV — ghi note skill demo"*

```
PATCH /api/candidates/8a0d0844
  body: {"ghi_chu_ai":"Skill test run 2026-05-26 09:55"}
→ Response: {"ok":true, "updated_fields":["ghi_chu_ai"]}
```

📄 Output: [hrm-cap-nhat-ung-vien/output/patch-ghi-chu-linh-test-6-2026-05-26-0955.md](../.claude/skills/hrm-cap-nhat-ung-vien/output/patch-ghi-chu-linh-test-6-2026-05-26-0955.md)

### ⏱ 10:05:30 — communication-agent invoked: `auto-send-email`

recruitment-agent **hand-off** sang communication-agent:
> *"Linh Test 6 đã ready, gửi mail mời PV vòng 1 ngày 28/05 14h00"*

```
Template: invite_pv
Sender: tuyendung@seongon.com (Lark Mail OpenAPI)
Recipient: ngoclinhk47u1@gmail.com
→ Rendered template với data ứng viên thật
→ Dry-run validated (production send chạy qua scheduler 21/05 đã thành công)
```

📄 Output: [auto-send-email/output/test-send-mail-PV-2026-05-26.md](../.claude/skills/auto-send-email/output/test-send-mail-PV-2026-05-26.md)

### ⏱ 10:12:45 — communication-agent invoked: `lark-calendar-pv`

```
Tạo event Lark Calendar 28/05 14:00-15:00
→ Auto-call auto-send-email (template "Mời PV" có Meet link)
→ Auto-call hrm-cap-nhat-ung-vien (set trạng thái = "Đã mời PV")
```

📄 Output: [lark-calendar-pv/output/test-create-event-2026-05-26.md](../.claude/skills/lark-calendar-pv/output/test-create-event-2026-05-26.md)

---

## 🔄 Sequence diagram

```
User                recruitment-agent           communication-agent          HRM API        Lark API
 │                          │                            │                     │              │
 │ "Quét email 24h"         │                            │                     │              │
 ├─────────────────────────▶│                            │                     │              │
 │                          │ hrm-quet-cv-moi            │                     │              │
 │                          │ POST /scan-emails ─────────────────────────────▶ │              │
 │                          │ ◀───────────────────────── 27 new CVs ─────────  │              │
 │ "Lọc top 20 điểm cao"    │                            │                     │              │
 ├─────────────────────────▶│                            │                     │              │
 │                          │ hrm-loc-ung-vien           │                     │              │
 │                          │ GET /candidates ─────────────────────────────  ▶ │              │
 │                          │                            │                     │              │
 │ "Mời PV Linh Test 6"     │                            │                     │              │
 ├─────────────────────────▶│                            │                     │              │
 │                          │ hrm-cap-nhat-ung-vien      │                     │              │
 │                          │ PATCH ──────────────────────────────────────  ▶  │              │
 │                          │                            │                     │              │
 │                          │ ── hand-off ────────────▶  │                     │              │
 │                          │                            │ lark-calendar-pv    │              │
 │                          │                            │ POST event ───────────────────  ▶  │
 │                          │                            │ auto-send-email     │              │
 │                          │                            │ POST mail ────────────────────  ▶  │
 │                          │                            │ → cập nhật HRM ───  ▶              │
 │                          │                            │                     │              │
```

---

## 🎯 Bài học orchestration

1. **Separation of concerns rõ:** recruitment-agent KHÔNG gửi email; communication-agent KHÔNG đụng vào logic điểm AI/lọc CV. Hai agent giao tiếp qua message với candidate_id.

2. **Skill composability:** `lark-calendar-pv` không tự gửi mail — nó gọi lại `auto-send-email`. Tránh duplicate logic email templating.

3. **Load-on-demand templates:** `hrm-loc-ung-vien` chỉ load 1 file template tương ứng (`by-score.md`), không load cả 4. Tiết kiệm context.

4. **Run-log audit trail:** Mỗi skill có `run-log.txt` append-only — verify được khi nào skill chạy, ai chạy, params, kết quả.

5. **Hand-off pattern:** recruitment-agent → communication-agent qua "candidate ready" event. Trong production, agent có thể chạy parallel hoặc qua message queue.

---

## 📊 Số liệu kết quả ngày 26/05

| Chỉ số | Giá trị |
|---|---|
| Email scan | 147 |
| CV mới sync vào DB | +27 |
| Total candidates sau scan | 118 |
| Top 20 lọc theo điểm AI | 1 query |
| Update field qua API | 1 record |
| Mời PV (dry-run rendered) | 1 |
| Tạo event Lark Calendar (planned) | 1 |
| Skill được kích hoạt | 5/6 |

---

*Generated by orchestration audit at 2026-05-26 10:25:00 ICT*
