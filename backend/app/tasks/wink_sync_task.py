"""
Celery task for Wink inventory sync
"""
import sys
import os
from celery import Task
from app.infrastructure.celery_app import celery_app
from app.infrastructure.database import JobRepository
from app.domain.models import JobStatus
from app.config import get_settings

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from noco_wink_inventory_sync.nocodb_manager import NocoDBManager
from noco_wink_inventory_sync.wink_inventory_sync import WinkInventorySync


class CallbackTask(Task):
    """Task with progress callback support"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        job_id = args[0] if args else None
        if job_id:
            repo = JobRepository()
            job = repo.get_job(job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.completed_at = retval.get("completed_at") if isinstance(retval, dict) else None
                job.stats = retval if isinstance(retval, dict) else {"result": retval}
                job.logs.append("Sync completed successfully")
                repo.update_job(job)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        job_id = args[0] if args else None
        if job_id:
            repo = JobRepository()
            job = repo.get_job(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.logs.append(f"Sync failed: {str(exc)}")
                repo.update_job(job)


@celery_app.task(bind=True, base=CallbackTask, name="sync_wink_inventory")
def sync_wink_inventory(self, job_id: str):
    """
    Celery task to sync Wink inventory
    
    Args:
        job_id: Job ID for tracking
        
    Returns:
        Dictionary with sync statistics
    """
    settings = get_settings()
    repo = JobRepository()
    
    # Update job status to running
    job = repo.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    job.status = JobStatus.RUNNING
    job.progress = 0
    job.logs.append("Starting Wink inventory sync...")
    repo.update_job(job)
    
    try:
        # Initialize NocoDB manager
        nocodb_manager = NocoDBManager(
            api_token=settings.nocodb_api_token,
            base_url=settings.nocodb_base_url,
            project_name=settings.nocodb_project_name,
            table_name=settings.nocodb_table_name
        )
        
        # Initialize Wink sync
        wink_sync = WinkInventorySync(
            nocodb_manager=nocodb_manager,
            wink_api_base_url=settings.wink_api_base_url,
            account_id=settings.wink_account_id,
            username=settings.wink_username,
            password=settings.wink_password,
            store_id=settings.wink_store_id
        )
        
        # Run sync
        job.logs.append("Authenticating with Wink API...")
        repo.update_job(job)
        
        stats = wink_sync.sync_inventory()
        
        # Update job with results
        job.progress = 100
        job.stats = stats
        job.logs.append(f"Sync completed: {stats.get('updated', 0)} records updated")
        repo.update_job(job)
        
        return stats
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.logs.append(f"Error: {str(e)}")
        repo.update_job(job)
        raise

