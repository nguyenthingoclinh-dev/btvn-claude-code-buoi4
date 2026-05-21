"""Chạy rejection_mail_agent theo lịch 30 phút/lần.
Khởi động:  nohup .venv/bin/python rejection_scheduler.py > rejection_agent.log 2>&1 &
"""

import logging
import time

import schedule

from rejection_mail_agent import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("rejection_agent.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("rejection-scheduler")

# Chạy ngay khi start + mỗi 30 phút sau đó
run_once()
schedule.every(30).minutes.do(run_once)

log.info("Rejection scheduler started — chạy mỗi 30 phút")
while True:
    schedule.run_pending()
    time.sleep(30)
