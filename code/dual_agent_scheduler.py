"""Chạy CẢ 2 agents song song mỗi 30 phút.
   - Agent #1: interview_invite_agent (gửi thư mời PV)
   - Agent #2: rejection_mail_agent (gửi thư từ chối)

Đây là layer dự phòng — main path là backend tự trigger real-time khi PATCH.
Scheduler này quét backup mỗi 30' để bắt các case lọt (đổi data ngoài
dashboard, backend crash, agent run failed retry...).

Khởi động:  nohup .venv/bin/python dual_agent_scheduler.py > dual_agent.log 2>&1 &
"""

import logging
import time

import schedule

from interview_invite_agent import run_once as run_invite_agent
from rejection_mail_agent import run_once as run_rejection_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("dual_agent.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("dual-scheduler")


def run_both():
    log.info("════════ Quét cả 2 agents ════════")
    try:
        run_invite_agent()
    except Exception:
        log.exception("invite agent failed")
    try:
        run_rejection_agent()
    except Exception:
        log.exception("rejection agent failed")
    log.info("════════ Done both agents ════════\n")


# Chạy ngay khi start + mỗi 30 phút sau đó
run_both()
schedule.every(30).minutes.do(run_both)

log.info("Dual agent scheduler started — chạy cả Invite + Rejection mỗi 30 phút")
while True:
    schedule.run_pending()
    time.sleep(30)
