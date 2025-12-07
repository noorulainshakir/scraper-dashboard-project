"""
Domain models for jobs and schedules
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job model"""
    id: str
    status: JobStatus
    progress: int = 0
    stats: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    celery_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "stats": self.stats,
            "logs": self.logs,
            "error": self.error,
            "celery_task_id": self.celery_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Schedule:
    """Schedule model"""
    id: str
    job_type: str  # e.g., "wink-sync"
    frequency: Optional[str] = None  # "daily", "weekly", "hourly"
    cron_expression: Optional[str] = None  # Cron format: "0 2 * * *"
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary"""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "frequency": self.frequency,
            "cron_expression": self.cron_expression,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

