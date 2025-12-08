"""
WebSocket endpoints for live updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import List

from app.infrastructure.websocket_manager import manager
from app.services.job_service import JobService

router = APIRouter()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live job logs"""
    await manager.connect(websocket)
    job_service = JobService()
    
    try:
        while True:
            # Get all recent jobs (running, pending, or recently completed)
            from app.domain.models import JobStatus
            recent_jobs = job_service.list_jobs(status=None, limit=50)
            
            # Send updates for each job (including progress updates)
            for job in recent_jobs:
                # Send update if job is active or recently completed
                if job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]:
                    await websocket.send_json({
                        "job_id": job.id,
                        "status": job.status.value,
                        "progress": job.progress,
                        "latest_log": job.logs[-1] if job.logs else None,
                        "logs_count": len(job.logs)
                    })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

