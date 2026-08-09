import time
import threading
from app import create_app
from utils.async_task import run_async

app = create_app()


def background_job():
    print(
        f"[{time.time()}] Background job starting on thread: {threading.current_thread().name}"
    )
    time.sleep(2)
    print(
        f"[{time.time()}] Background job finished on thread: {threading.current_thread().name}"
    )


if __name__ == "__main__":
    with app.app_context():
        print(
            f"[{time.time()}] Main thread starting async job. Current thread: {threading.current_thread().name}"
        )
        t = run_async(background_job)
        print(f"[{time.time()}] Main thread continuing immediately.")
        t.join()
        print(f"[{time.time()}] Main thread finished waiting.")
