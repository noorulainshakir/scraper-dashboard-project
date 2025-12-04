from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "wink_sync_tasks",
    broker=redis_url,
    backend=redis_url
)
