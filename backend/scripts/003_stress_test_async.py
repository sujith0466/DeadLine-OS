import time
import sys
import os
import threading
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from utils.async_task import run_async

logging.basicConfig(level=logging.INFO, format="[STRESS] %(message)s")
logger = logging.getLogger(__name__)

completed_jobs = 0
lock = threading.Lock()


def lightweight_job(job_id):
    global completed_jobs
    time.sleep(0.1)  # Simulate some minor IO
    with lock:
        completed_jobs += 1


def stress_test():
    app = create_app()
    with app.app_context():
        logger.info("Starting 100 parallel async jobs...")

        threads = []
        for i in range(100):
            t = run_async(lightweight_job, i)
            threads.append(t)

        logger.info("All jobs fired. Main thread waiting for completion...")
        for t in threads:
            t.join()

        logger.info(f"Stress test complete. Completed jobs: {completed_jobs}")
        if completed_jobs == 100:
            logger.info("Result: PASS (No thread leaks, deadlocks, or crashes)")
        else:
            logger.error("Result: FAIL (Some jobs did not complete)")


if __name__ == "__main__":
    stress_test()
