"""
Celery application setup
"""
from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "scraper_dashboard",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.wink_sync_task"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.job_timeout,
    task_soft_time_limit=settings.job_timeout - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Import tasks to register them
from app.tasks import wink_sync_task
from app.tasks import celery_beat

