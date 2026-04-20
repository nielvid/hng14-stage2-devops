import redis
import time
import os
import signal
import sys

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)

running = True


def shutdown_handler(signum, frame):
    global running
    print("Shutting down gracefully...")
    running = False


# Listen for termination signals
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


def process_job(job_id):
    print(f"Processing job {job_id}")
    time.sleep(2)  # simulate work
    r.hset(f"job:{job_id}", "status", "completed")
    print(f"Done: {job_id}")


while running:
    job = r.brpop("job", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id.decode())

print("Worker stopped cleanly")
sys.exit(0)
