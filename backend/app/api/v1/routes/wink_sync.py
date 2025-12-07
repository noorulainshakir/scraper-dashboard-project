"""
Wink sync API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.services.job_service import JobService
from app.services.scheduler_service import SchedulerService
from app.domain.models import JobStatus
from app.core.exceptions import JobNotFoundError, JobNotRunningError

router = APIRouter(prefix="/services/wink-sync", tags=["wink-sync"])


def get_job_service() -> JobService:
    """Dependency for job service"""
    return JobService()


def get_scheduler_service() -> SchedulerService:
    """Dependency for scheduler service"""
    return SchedulerService()


@router.post("/start")
def start_sync(service: JobService = Depends(get_job_service)):
    """Start a new Wink inventory sync job"""
    try:
        job = service.start_sync()
        return {
            "job_id": job.id,
            "status": job.status.value,
            "celery_task_id": job.celery_task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
def get_status(job_id: str, service: JobService = Depends(get_job_service)):
    """Get sync job status"""
    try:
        job = service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job.to_dict()
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/stop/{job_id}")
def stop_sync(job_id: str, service: JobService = Depends(get_job_service)):
    """Stop a running sync job"""
    try:
        job = service.stop_job(job_id)
        return {
            "job_id": job.id,
            "status": job.status.value,
            "message": "Job stopped successfully"
        }
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except JobNotRunningError:
        raise HTTPException(status_code=400, detail="Job is not running")


@router.get("/logs/{job_id}")
def get_logs(job_id: str, service: JobService = Depends(get_job_service)):
    """Get sync job logs"""
    try:
        logs = service.get_job_logs(job_id)
        return {
            "job_id": job_id,
            "logs": logs
        }
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/jobs")
def list_jobs(
    status: str = None,
    limit: int = 100,
    service: JobService = Depends(get_job_service)
):
    """List all jobs, optionally filtered by status"""
    job_status = JobStatus(status) if status else None
    jobs = service.list_jobs(status=job_status, limit=limit)
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": len(jobs)
    }


@router.post("/schedule")
def create_schedule(
    frequency: str = None,
    cron: str = None,
    scheduler: SchedulerService = Depends(get_scheduler_service)
):
    """Create a schedule for automatic sync"""
    if not frequency and not cron:
        raise HTTPException(status_code=400, detail="Either frequency or cron expression required")
    
    try:
        schedule = scheduler.create_schedule(
            job_type="wink-sync",
            frequency=frequency,
            cron_expression=cron
        )
        return {
            "schedule_id": schedule.id,
            "scheduled": True,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "schedule": schedule.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

