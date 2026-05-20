# BTVN Buổi 4 — Khoá Claude Code (Agent Boss Starter)

> **Học viên:** Nguyễn Thị Ngọc Linh — HRM SEONGON
> **Mentor:** Mai Xuân Đạt
> **Ngày nộp:** 20/05/2026

---

## 🎯 Đề bài buổi 4

Từ kết quả BTVN buổi 3 (HRM SEONGON dashboard), **nâng cấp không gian làm việc** bằng cách xây dựng:
- **≥ 2 agents** (`.claude/agents/`)
- **≥ 2 SKILLS mỗi agent** (`.claude/skills/`)

Sau đó giao **1 nhiệm vụ lớn** cho Claude Code và để nó tự phân bổ cho các sub-agent phù hợp.

## 📋 Nhiệm vụ lớn đã giao trong session này

> _"Tôi muốn làm 1 con Agent tự động hoá tuyển dụng: khi ứng viên trong HRM đổi trạng thái **'Quản lý đã duyệt'** + Tình trạng **'Phù hợp'** + có **'Lịch phỏng vấn'** → tự động gửi Email mời PV qua `tuyendung@seongon.com`, báo Lark, tạo lịch Lark Calendar. Bổ sung cột **'Đã gửi Email'** + nút **'Gửi lại'** lên dashboard."_

✅ **Hoàn thành 100% end-to-end** — Claude Code chính tự phân bổ cho 2 sub-agents:
- `recruitment-agent` (thao tác HRM API, query ứng viên, PATCH status)
- `communication-agent` (Lark Mail send, Lark IM notify, Lark Calendar create)

---

## 📂 Cấu trúc repo

```
btvn-claude-code-buoi4/
├── README.md                              ← bạn đang đọc
├── .claude/
│   ├── agents/                            ← 2 sub-agents
│   │   ├── recruitment-agent.md
│   │   └── communication-agent.md
│   └── skills/                            ← 6 skills (≥2 mỗi agent)
│       ├── auto-send-email/               ← Lark Mail OpenAPI + 4 templates
│       ├── lark-setup-bot/                ← Lark IM bot setup
│       ├── lark-calendar-pv/              ← Lark Calendar event PV
│       ├── hrm-quet-cv-moi/               ← Scan email → CV
│       ├── hrm-loc-ung-vien/              ← Lọc ứng viên đa tiêu chí
│       └── hrm-cap-nhat-ung-vien/         ← PATCH HRM API
├── code/                                  ← Source code agent xây trong session
│   ├── interview_invite_agent.py          ← Logic chính (≈360 dòng)
│   ├── interview_scheduler.py             ← Cron 30 phút/lần
│   ├── refresh_lark_token.py              ← OAuth helper
│   ├── inspect_lark_base.py               ← Debug helper
│   ├── list_lark_tables.py                ← Discover schema
│   ├── test_send_lark_mail.py             ← Test gửi mail standalone
│   ├── requirements.txt
│   ├── .env.example                       ← Mẫu env, KHÔNG kèm secret
│   └── hrm-backend-additions/             ← Code thêm vào HRM repo
│       ├── lark_mail.py                   ← NEW module gửi mail backend
│       └── hrm-changes.diff               ← Diff db.py / app.py / index.html
├── outputs/                               ← Kết quả chạy thật
│   ├── agent-run-log.txt                  ← Log agent gửi thành công
│   ├── email-received.png                 ← Screenshot inbox (ứng viên nhận)
│   ├── hrm-dashboard-da-gui-email.png     ← Screenshot cột "Đã gửi Email"
│   └── lark-im-notification.png           ← Screenshot Lark IM báo HRM
├── conv/
│   └── README.md                          ← Hướng dẫn export chat history
└── docs/
    └── ARCHITECTURE.md                    ← Sơ đồ phân bổ agent
```

---

## 🤖 2 Agents (sub-agent)

### 1. `recruitment-agent`
> Chuyên gia quản lý ứng viên HRM SEONGON — đọc/lọc/cập nhật pipeline trên `ngoclinhhrm.com/tuyen-dung`.

| Skill sử dụng | Mục đích |
|---------------|----------|
| [`hrm-quet-cv-moi`](.claude/skills/hrm-quet-cv-moi/SKILL.md) | Quét email tuyển dụng → đồng bộ CV mới |
| [`hrm-loc-ung-vien`](.claude/skills/hrm-loc-ung-vien/SKILL.md) | Lọc ứng viên theo vị trí / điểm AI / trạng thái |
| [`hrm-cap-nhat-ung-vien`](.claude/skills/hrm-cap-nhat-ung-vien/SKILL.md) | PATCH trạng thái / tình trạng / bài test / file PV |

### 2. `communication-agent`
> Chuyên gia communication tự động — Email + Lark IM + Lark Calendar.

| Skill sử dụng | Mục đích |
|---------------|----------|
| [`auto-send-email`](.claude/skills/auto-send-email/SKILL.md) | Gửi email từ `tuyendung@seongon.com` qua Lark Mail OpenAPI (4 templates) |
| [`lark-setup-bot`](.claude/skills/lark-setup-bot/SKILL.md) | Setup Lark Bot + gửi IM text/card |
| [`lark-calendar-pv`](.claude/skills/lark-calendar-pv/SKILL.md) | Tạo Lark Calendar event PV, mời attendees |

---

## ⚙️ Cách Claude Code phân bổ task

```
User: "Tôi muốn làm 1 con Agent tự động hoá tuyển dụng…"
                    ↓
        ┌───────────────────────┐
        │   Claude Code (main)  │
        │   Phân tích task lớn  │
        └──────────┬────────────┘
                   │
        ┌──────────┴──────────────┐
        ↓                         ↓
┌──────────────────┐    ┌──────────────────────┐
│ recruitment-agent│    │ communication-agent  │
├──────────────────┤    ├──────────────────────┤
│ • Query HRM API  │    │ • Send Lark Mail     │
│ • Filter 3 ĐK    │    │ • Send Lark IM       │
│ • PATCH status   │    │ • Create Calendar    │
│   sent/failed    │    │   event              │
└──────────────────┘    └──────────────────────┘
        │                         │
        └──────────┬──────────────┘
                   ↓
        ┌──────────────────────┐
        │   Output đầu ra      │
        │ • Email tới ứng viên │
        │ • Lark IM cho HRM    │
        │ • Calendar event     │
        │ • Cột status + nút   │
        │   Gửi lại            │
        └──────────────────────┘
```

---

## ✅ Kết quả thực tế

| Output | Bằng chứng |
|--------|------------|
| Email gửi thành công cho `ngoclinhk47u1@gmail.com` | `outputs/email-received.png` |
| Lark IM cho HRM | `outputs/lark-im-notification.png` |
| Lark Calendar event 10:30 21/05/2026 (60 phút) | `outputs/agent-run-log.txt` |
| HRM dashboard hiển thị cột "Đã gửi Email" với timestamp + nút Gửi lại | `outputs/hrm-dashboard-da-gui-email.png` |
| Backend deployed Cloud Run rev `hrm-api-00054-dh8` | `outputs/agent-run-log.txt` |
| Frontend deployed Cloudflare Pages | `https://ngoclinhhrm.com/tuyen-dung/` |

---

## 📜 RUBRIC chấm bài (đối chiếu)

| # | Tiêu chí | Status |
|---|----------|--------|
| 1 | Files & folder code trên 1 repo Github | ✅ Repo này |
| 1.a | Có folder `.claude/` | ✅ |
| 1.b | Trong `.claude/` có `/skills` và `/agents` | ✅ |
| 2 | File ghi chép lịch sử chat với Claude Code (`/export`) | ✅ `conv/chat-history.txt` |
| 3 | Các file output từ việc giao việc cho Agent và sử dụng SKILLS | ✅ `outputs/` |
| ≥ 2 agents | ✅ `recruitment-agent` + `communication-agent` |
| ≥ 2 skills mỗi agent | ✅ 3 skills mỗi agent (6 skills tổng) |

---

## 🚀 Cách chạy lại (re-produce)

```bash
# 1. Cài deps
cd code/
pip install -r requirements.txt

# 2. Cấu hình env
cp .env.example .env
# → điền LARK_APP_ID, LARK_APP_SECRET, CV_NOTIFY_USER_ID

# 3. Authorize OAuth (1 lần đầu — mở browser)
python refresh_lark_token.py
# → click URL → authorize → paste lại code:
python refresh_lark_token.py <code>

# 4. Chạy agent
python interview_invite_agent.py        # chạy 1 lần
python interview_scheduler.py           # chạy nền 30 phút/lần
```

---

## 🔗 Links

- **HRM Dashboard live:** https://ngoclinhhrm.com/tuyen-dung/
- **HRM API base:** https://hrm-api-521103150103.asia-southeast1.run.app
- **Repo BTVN buổi 3 (HRM system):** https://github.com/nguyenthingoclinh-dev/btvn-claude-code-buoi3
- **Khoá học:** [Agent Boss Starter](https://maixuandat.com/agent-boss-starter)
