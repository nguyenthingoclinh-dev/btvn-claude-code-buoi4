"""
Lịch chạy Interview Invite Agent.
Quét mỗi 30 phút trong giờ làm việc 08:00–18:30 (GMT+7).
Khởi động: python interview_scheduler.py
"""

import logging
import time

import schedule

from interview_invite_agent import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("interview_agent.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("interview-scheduler")

# Chạy mỗi 30 phút (schedule không có timezone-aware nên dùng giờ hệ thống — đảm bảo server đặt Asia/Ho_Chi_Minh)
schedule.every(30).minutes.do(run_once)

if __name__ == "__main__":
    log.info("Interview Scheduler started — quét mỗi 30 phút")
    run_once()          # chạy ngay khi khởi động
    while True:
        schedule.run_pending()
        time.sleep(30)
