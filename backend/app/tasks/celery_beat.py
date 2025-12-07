"""
Celery Beat scheduler configuration
"""
from celery.schedules import crontab
from app.infrastructure.celery_app import celery_app

# Celery Beat schedule
# Note: Dynamic schedules are loaded from database at runtime
# Add periodic task to check schedules every minute
celery_app.conf.beat_schedule = {
    'check-schedules': {
        'task': 'check_and_run_schedules',
        'schedule': 60.0,  # Every 60 seconds
    },
}

celery_app.conf.timezone = 'UTC'


@celery_app.task(name="check_and_run_schedules")
def check_and_run_schedules():
    """Periodically check schedules and run jobs"""
    from datetime import datetime, timedelta
    from croniter import croniter
    from app.services.scheduler_service import SchedulerService
    from app.services.job_service import JobService
    
    scheduler = SchedulerService()
    job_service = JobService()
    schedules = scheduler.list_schedules()
    
    now = datetime.utcnow()
    
    for schedule in schedules:
        if not schedule.enabled or schedule.job_type != "wink-sync":
            continue
        
        # Check if it's time to run
        if schedule.next_run and schedule.next_run <= now:
            # Start the job
            job = job_service.start_sync()
            
            # Update schedule - calculate next run
            if schedule.cron_expression:
                cron = croniter(schedule.cron_expression, now)
                schedule.next_run = cron.get_next(datetime)
            elif schedule.frequency == "daily":
                schedule.next_run = now + timedelta(days=1)
            elif schedule.frequency == "hourly":
                schedule.next_run = now + timedelta(hours=1)
            elif schedule.frequency == "weekly":
                schedule.next_run = now + timedelta(weeks=1)
            
            schedule.last_run = now
            scheduler._save_schedule(schedule)

