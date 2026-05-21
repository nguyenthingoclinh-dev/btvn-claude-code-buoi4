# BTVN Buổi 4 — Khoá Claude Code tại SEONGON

> **Học viên:** Nguyễn Thị Ngọc Linh — HRM SEONGON
> **Ngày nộp:** 21/05/2026

---

## Đề bài buổi 4

Từ kết quả BTVN buổi 3 (HRM SEONGON dashboard), **nâng cấp không gian làm việc** bằng cách xây dựng:
- **>= 2 agents** (`.claude/agents/`)
- **>= 2 SKILLS mỗi agent** (`.claude/skills/`)

Sau đó giao **1 nhiệm vụ lớn** cho Claude Code và để nó tự phân bổ cho các sub-agent phù hợp.

## Nhiệm vụ lớn đã giao trong session

> _"Tôi muốn webapp HRM có 2 Agent chạy đồng thời:
> Agent 1 — Tự động gửi thư mời PV khi ứng viên ở trạng thái 'Quản lý đã duyệt' + 'Phù hợp' + có Lịch PV.
> Agent 2 — Tự động gửi thư từ chối khi Tình trạng = 'Không phù hợp'.
> Cả 2 phải báo Lark IM cho HRM sau khi gửi. Có cột 'Đã gửi Email' + nút 'Gửi lại' trên dashboard.
> Khi đổi Tình trạng Phù hợp <-> Không phù hợp thì gửi đúng email tương ứng (kể cả khi đã gửi lần trước)."_

Hoàn thành 100% end-to-end. Claude Code chính tự phân bổ cho 2 sub-agents:
- `recruitment-agent` (thao tác HRM API, query ứng viên, PATCH status, snapshot trước/sau để detect transition)
- `communication-agent` (Lark Mail send 2 loại template, Lark IM notify, Lark Calendar create)

---

## Cấu trúc repo

```
btvn-claude-code-buoi4/
├── README.md                              <- bạn đang đọc
├── .claude/
│   ├── agents/                            <- 2 sub-agents
│   │   ├── recruitment-agent.md
│   │   └── communication-agent.md
│   └── skills/                            <- 6 skills (>=2 mỗi agent)
│       ├── auto-send-email/               <- Lark Mail OpenAPI + 4 templates
│       ├── lark-setup-bot/                <- Lark IM bot setup
│       ├── lark-calendar-pv/              <- Lark Calendar event PV
│       ├── hrm-quet-cv-moi/               <- Scan email -> CV
│       ├── hrm-loc-ung-vien/              <- Loc ung vien da tieu chi
│       └── hrm-cap-nhat-ung-vien/         <- PATCH HRM API
├── code/                                  <- Source code agent xay trong session
│   ├── interview_invite_agent.py          <- Agent #1 - moi PV
│   ├── interview_scheduler.py             <- Cron Agent #1
│   ├── rejection_mail_agent.py            <- Agent #2 - tu choi
│   ├── rejection_scheduler.py             <- Cron Agent #2
│   ├── dual_agent_scheduler.py            <- Chay ca 2 agent moi 30 phut (backup)
│   ├── refresh_lark_token.py              <- OAuth helper
│   ├── inspect_lark_base.py               <- Debug helper
│   ├── list_lark_tables.py                <- Discover schema
│   ├── test_send_lark_mail.py             <- Test gui mail standalone
│   ├── requirements.txt
│   ├── .env.example                       <- Mau env, KHONG kem secret
│   └── hrm-backend-additions/             <- Code them vao HRM repo
│       ├── lark_mail.py                   <- Module gui mail + IM backend
│       ├── sync_lark_token.py             <- Sync token local -> Firestore
│       ├── seed_test_candidates.py        <- Seed 5 ung vien test
│       └── hrm-changes.diff               <- Diff db.py / app.py / index.html
├── outputs/                               <- Ket qua chay that
│   ├── agent-run-log.txt                  <- Log ca 2 agent gui thanh cong
│   └── README.md
├── conv/
│   ├── README.md                          <- Huong dan export chat history
│   └── chat-history-clean.txt             <- Bien ban session da clean
└── docs/
    └── ARCHITECTURE.md                    <- So do phan bo agent + token flow
```

---

## 2 Agents (sub-agent)

### 1. `recruitment-agent`
> Chuyên gia quản lý ứng viên HRM SEONGON — đọc/lọc/cập nhật pipeline trên `ngoclinhhrm.com/tuyen-dung`.

| Skill sử dụng | Mục đích |
|---------------|----------|
| [`hrm-quet-cv-moi`](.claude/skills/hrm-quet-cv-moi/SKILL.md) | Quét email tuyển dụng -> đồng bộ CV mới |
| [`hrm-loc-ung-vien`](.claude/skills/hrm-loc-ung-vien/SKILL.md) | Lọc ứng viên theo vị trí / điểm AI / trạng thái |
| [`hrm-cap-nhat-ung-vien`](.claude/skills/hrm-cap-nhat-ung-vien/SKILL.md) | PATCH trạng thái / tình trạng / bài test / file PV / email status |

### 2. `communication-agent`
> Chuyên gia communication tự động — Email + Lark IM + Lark Calendar.

| Skill sử dụng | Mục đích |
|---------------|----------|
| [`auto-send-email`](.claude/skills/auto-send-email/SKILL.md) | Gửi email từ `tuyendung@seongon.com` qua Lark Mail OpenAPI (4 templates: mời PV, cảm ơn, từ chối, trúng tuyển) |
| [`lark-setup-bot`](.claude/skills/lark-setup-bot/SKILL.md) | Setup Lark Bot + gửi IM text/card |
| [`lark-calendar-pv`](.claude/skills/lark-calendar-pv/SKILL.md) | Tạo Lark Calendar event PV, mời attendees |

---

## Cách Claude Code phân bổ task

```
User: "Webapp HRM phai co 2 Agent chay dong thoi..."
                    |
        +-------------------------+
        |   Claude Code (main)    |
        |   Phan tich task lon    |
        +-----------+-------------+
                    |
        +-----------+---------------+
        |                           |
        v                           v
+------------------+    +----------------------+
| recruitment-agent|    | communication-agent  |
+------------------+    +----------------------+
| - Query HRM API  |    | - Send Lark Mail     |
| - Snapshot       |    | - Send Lark IM       |
|   before/after   |    | - Create Calendar    |
| - Detect         |    |   event              |
|   transition     |    | - 4 mail templates   |
| - PATCH status   |    +----------------------+
|   sent/failed    |
+------------------+
        |                           |
        +-----------+---------------+
                    v
        +---------------------------+
        |   Output dau ra           |
        | - Email moi PV / tu choi  |
        | - Lark IM cho HRM         |
        | - Calendar event          |
        | - Cot "Da gui Email"      |
        | - Nut "Gui lai" / action  |
        +---------------------------+
```

---

## Kết quả thực tế

| Output | Trạng thái |
|--------|------------|
| Email mời PV gửi thành công cho `ngoclinhk47u1@gmail.com` | 1 lượt |
| Email từ chối gửi thành công cho `ngoclinhk47u1@gmail.com` | 6 lượt |
| Lark IM báo HRM mỗi lần gửi | 7 lượt |
| Lark Calendar event PV | 1 |
| Tổng ứng viên trong HRM | 90 |
| Real-time trigger từ backend khi PATCH | OK |
| Cron scheduler 30 phút (dự phòng) | OK |
| Backend deployed Cloud Run | rev `hrm-api-00059-j8f` |
| Frontend deployed Cloudflare Pages | `https://ngoclinhhrm.com/tuyen-dung/` |

---

## RUBRIC chấm bài (đối chiếu)

| # | Tiêu chí | Status |
|---|----------|--------|
| 1 | Files & folder code trên 1 repo Github | OK - repo này |
| 1.a | Có folder `.claude/` | OK |
| 1.b | Trong `.claude/` có `/skills` và `/agents` | OK |
| 2 | File ghi chép lịch sử chat (`/export`) | OK - `conv/chat-history-clean.txt` |
| 3 | Các file output từ việc giao việc cho Agent | OK - `outputs/` |
| >= 2 agents | OK - recruitment + communication |
| >= 2 skills mỗi agent | OK - 3 skills mỗi agent (6 skills tổng) |

---

## Cách chạy lại (re-produce)

```bash
# 1. Cài deps
cd code/
pip install -r requirements.txt

# 2. Cấu hình env
cp .env.example .env
# -> điền LARK_APP_ID, LARK_APP_SECRET, CV_NOTIFY_USER_ID

# 3. Authorize OAuth (1 lần đầu - mở browser)
python refresh_lark_token.py
# -> click URL -> authorize -> paste lại code:
python refresh_lark_token.py <code>

# 4. Chạy cả 2 agent cùng lúc (cron 30 phút)
python dual_agent_scheduler.py

# HOẶC chạy riêng từng cái 1 lần:
python interview_invite_agent.py        # Agent #1
python rejection_mail_agent.py          # Agent #2
```

---

## Pipeline hoàn chỉnh (zero-touch)

```
1. CV gui -> tuyendung@seongon.com
2. cv_processor scan email moi 4h -> AI extract + danh gia
3. Len dashboard ngoclinhhrm.com (HRM thay + duyet)
4. HRM bam "Duyet" + chon Lich PV + doi Tinh trang "Phu hop"
5. Backend tu dong (~2 giay):
   - Gui email moi PV -> ung vien
   - Gui Lark IM -> HRM
   - Tao Calendar event PV
   - Cap nhat dashboard cot "Da gui Email"
6. Neu HRM doi sang "Khong phu hop":
   - Gui email tu choi -> ung vien
   - Gui Lark IM -> HRM
   - Cap nhat dashboard cot "Da gui Email"
7. Toggle Phu hop <-> Khong phu hop:
   - Moi lan toggle = gui email tuong ung (detect transition,
     force re-send, khong silent skip)
```

---

## 4 bug đã fix trong session

| # | Bug | Nguyên nhân | Fix |
|---|-----|-------------|-----|
| 1 | `code=20043` | App thiếu scope `mail:user_mailbox.message:send` | Add scope + publish v1.3.5 + admin approve |
| 2 | `code=99991663` | Lark Mail không nhận tenant token | Đổi sang user OAuth token |
| 3 | Email body hiển thị base64 | Đã base64 encode body trước khi gửi | Bỏ base64, gửi HTML plain |
| 4 | `code=20038` -> `99991679` | Refresh token rotate single-use + token local khác Firestore | Auto save rotated token + script `sync_lark_token.py` |

---

## Links

- **HRM Dashboard live:** https://ngoclinhhrm.com/tuyen-dung/
- **HRM API base:** https://hrm-api-521103150103.asia-southeast1.run.app
- **Repo BTVN buổi 3 (HRM system):** https://github.com/nguyenthingoclinh-dev/btvn-claude-code-buoi3
- **Khoá học:** Claude Code tại SEONGON
