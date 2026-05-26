# Outputs — Kết quả thực tế từ session

Folder này chứa **tất cả output thật** sinh ra từ việc Claude Code thực thi nhiệm vụ.

> **⚠️ Nguyên tắc:** `.claude/skills/` CHỈ chứa skill spec + template, KHÔNG chứa output thực tế.
> Tất cả output đã chạy → lưu vào `outputs/<skill-name>/` (theo feedback của thầy giáo).

## Cấu trúc

### File task-level (story của BTVN buổi 4)

| File | Mô tả |
|------|-------|
| [`demo-orchestration.md`](./demo-orchestration.md) | Story: Claude Code nhận 1 nhiệm vụ lớn → phân bổ cho 2 sub-agents (recruitment + communication) |
| [`skill-usage-examples.md`](./skill-usage-examples.md) | 35+ skill invocations cụ thể trong session |
| [`agent-orchestration-2026-05-26.md`](./agent-orchestration-2026-05-26.md) | End-to-end flow ngày 26/05 (5 skill chạy nối tiếp) |
| [`agent-run-log.txt`](./agent-run-log.txt) | Log Python scheduler chạy thật trên Cloud Run 20-21/05 |

### Subfolder per-skill (output của từng skill khi được agent invoke)

| Folder | Skill thuộc agent nào | Output mới nhất |
|---|---|---|
| [`hrm-quet-cv-moi/`](./hrm-quet-cv-moi/) | recruitment-agent | Scan 147 email → +27 CV (08:35) |
| [`hrm-loc-ung-vien/`](./hrm-loc-ung-vien/) | recruitment-agent | Top 20 ứng viên điểm AI ≥ 70 (09:32) |
| [`hrm-cap-nhat-ung-vien/`](./hrm-cap-nhat-ung-vien/) | recruitment-agent | PATCH note Linh Test 6 (09:55) |
| [`auto-send-email/`](./auto-send-email/) | communication-agent | Render template mời PV (10:05) |
| [`lark-calendar-pv/`](./lark-calendar-pv/) | communication-agent | Tạo event 28/05 14:00 (10:12) |
| [`lark-setup-bot/`](./lark-setup-bot/) | communication-agent + hrm-security-agent | Setup checklist 10:20 + Security audit 10:48 |
| [`hrm-security-audit/`](./hrm-security-audit/) | hrm-security-agent | Audit repo: 0 Critical, 3 Medium (10:42) |

## Cách reproduce

```bash
cd ../code
pip install -r requirements.txt
cp .env.example .env
# Điền secret vào .env:
#   - LARK_APP_ID, LARK_APP_SECRET
#   - HRM_API_KEY (mới: KHÔNG paste plaintext vào file .md nào)
#   - CV_LARK_USER_REFRESH_TOKEN

# Authorize OAuth lần đầu
python refresh_lark_token.py
python refresh_lark_token.py <code>

# Chạy cả 2 agent
python dual_agent_scheduler.py
```

Sau khi chạy:
- Inbox ứng viên nhận email tương ứng
- Lark IM của HRM nhận tin báo
- Lark Calendar HRM có event PV
- Dashboard ngoclinhhrm.com cập nhật real-time
