"""
Job service for managing sync jobs
"""
import uuid
from typing import Optional, List
from celery.result import AsyncResult

from app.domain.models import Job, JobStatus
from app.infrastructure.database import JobRepository
from app.infrastructure.celery_app import celery_app
from app.tasks.wink_sync_task import sync_wink_inventory
from app.core.exceptions import JobNotFoundError, JobNotRunningError


class JobService:
    """Service for managing jobs"""
    
    def __init__(self):
        self.repo = JobRepository()
    
    def start_sync(self) -> Job:
        """Start a new Wink inventory sync job"""
        job_id = f"job_{str(uuid.uuid4())[:8]}"
        
        # Create job record
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            progress=0,
            logs=["Job created, queuing for execution..."]
        )
        job = self.repo.create_job(job)
        
        # Queue Celery task (with error handling)
        try:
            task = sync_wink_inventory.delay(job_id)
            job.celery_task_id = task.id
            job.status = JobStatus.RUNNING
            job.logs.append(f"Job queued with task ID: {task.id}")
        except Exception as e:
            # If Celery is not available, mark job as failed
            job.status = JobStatus.FAILED
            job.error = f"Failed to queue job: {str(e)}"
            job.logs.append(f"Error queuing job: {str(e)}")
        
        self.repo.update_job(job)
        
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        job = self.repo.get_job(job_id)
        if not job:
            return None
        
        # Update from Celery if running (with error handling)
        if job.celery_task_id and job.status == JobStatus.RUNNING:
            try:
                task_result = AsyncResult(job.celery_task_id, app=celery_app)
                if task_result.ready():
                    if task_result.successful():
                        job.status = JobStatus.COMPLETED
                        job.progress = 100
                    else:
                        job.status = JobStatus.FAILED
                        job.error = str(task_result.info) if task_result.info else "Task failed"
                    self.repo.update_job(job)
            except Exception:
                # If Celery is not available, just return the job as-is
                pass
        
        return job
    
    def stop_job(self, job_id: str) -> Job:
        """Stop a running job"""
        job = self.repo.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        if job.status != JobStatus.RUNNING:
            raise JobNotRunningError(f"Job {job_id} is not running")
        
        # Revoke Celery task (with error handling)
        if job.celery_task_id:
            try:
                celery_app.control.revoke(job.celery_task_id, terminate=True)
            except Exception:
                # If Celery is not available, just mark as stopped
                pass
        
        job.status = JobStatus.STOPPED
        job.logs.append("Job stopped by user")
        self.repo.update_job(job)
        
        return job
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[Job]:
        """List jobs"""
        return self.repo.list_jobs(status=status, limit=limit)
    
    def get_job_logs(self, job_id: str) -> List[str]:
        """Get logs for a job"""
        job = self.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job.logs

