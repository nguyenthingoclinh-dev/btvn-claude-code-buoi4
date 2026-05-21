# Outputs — Kết quả thực tế từ session

Tất cả file trong folder này là output thật từ việc Claude Code thực thi
nhiệm vụ lớn (xây 2 Agent gửi email tự động).

| File | Mô tả |
|------|-------|
| [`demo-orchestration.md`](./demo-orchestration.md) | Cách Claude Code phân tích 1 nhiệm vụ lớn và phân bổ cho 2 sub-agents (recruitment + communication), bao gồm input/output của mỗi sub-agent |
| [`skill-usage-examples.md`](./skill-usage-examples.md) | Chứng minh từng skill trong 6 skills đã được CALL thực tế, với input + output cụ thể (35+ skill invocations) |
| [`agent-run-log.txt`](./agent-run-log.txt) | Log chạy thật của 2 agent — Interview Invite Agent + Rejection Mail Agent, bao gồm 4 bug đã fix |

## Cách reproduce

```bash
cd ../code
pip install -r requirements.txt
cp .env.example .env  # rồi điền secret

# Authorize OAuth lần đầu
python refresh_lark_token.py
python refresh_lark_token.py <code>

# Chạy cả 2 agent
python dual_agent_scheduler.py

# Hoặc chạy 1 lần:
python interview_invite_agent.py   # Agent #1
python rejection_mail_agent.py     # Agent #2
```

Sau khi chạy:
- Inbox ứng viên nhận email tương ứng
- Lark IM của HRM nhận tin báo
- Lark Calendar HRM có event PV (nếu invite)
- Dashboard ngoclinhhrm.com cột "Đã gửi Email" cập nhật real-time
