"""
Database setup and job repository using SQLite
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os

from app.domain.models import Job, JobStatus


class JobRepository:
    """Repository for job persistence using SQLite"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    stats TEXT,
                    logs TEXT,
                    error TEXT,
                    celery_task_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Schedules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    frequency TEXT,
                    cron_expression TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_job(self, job: Job) -> Job:
        """Create a new job"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO jobs (id, status, progress, stats, logs, error, celery_task_id, 
                                created_at, updated_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.status.value,
                job.progress,
                json.dumps(job.stats) if job.stats else None,
                json.dumps(job.logs) if job.logs else None,
                job.error,
                job.celery_task_id,
                job.created_at,
                job.updated_at,
                job.started_at,
                job.completed_at
            ))
            conn.commit()
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return self._row_to_job(row)
    
    def update_job(self, job: Job) -> Job:
        """Update a job"""
        job.updated_at = datetime.utcnow()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs 
                SET status = ?, progress = ?, stats = ?, logs = ?, error = ?, 
                    celery_task_id = ?, updated_at = ?, started_at = ?, completed_at = ?
                WHERE id = ?
            """, (
                job.status.value,
                job.progress,
                json.dumps(job.stats) if job.stats else None,
                json.dumps(job.logs) if job.logs else None,
                job.error,
                job.celery_task_id,
                job.updated_at,
                job.started_at,
                job.completed_at,
                job.id
            ))
            conn.commit()
        return job
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[Job]:
        """List jobs, optionally filtered by status"""
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [self._row_to_job(row) for row in rows]
    
    def _row_to_job(self, row) -> Job:
        """Convert database row to Job model"""
        return Job(
            id=row["id"],
            status=JobStatus(row["status"]),
            progress=row["progress"],
            stats=json.loads(row["stats"]) if row["stats"] else None,
            logs=json.loads(row["logs"]) if row["logs"] else [],
            error=row["error"],
            celery_task_id=row["celery_task_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow(),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

