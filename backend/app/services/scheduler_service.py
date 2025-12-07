"""
Scheduler service for managing scheduled jobs
"""
import uuid
from datetime import datetime
from typing import Optional, List
from croniter import croniter

from app.domain.models import Schedule
from app.infrastructure.database import JobRepository
from app.services.job_service import JobService
from app.core.exceptions import ScheduleNotFoundError


class SchedulerService:
    """Service for managing scheduled jobs"""
    
    def __init__(self):
        self.repo = JobRepository()
        self.job_service = JobService()
    
    def create_schedule(
        self,
        job_type: str,
        frequency: Optional[str] = None,
        cron_expression: Optional[str] = None
    ) -> Schedule:
        """Create a new schedule"""
        schedule_id = f"schedule_{str(uuid.uuid4())[:8]}"
        
        # Calculate next run time
        next_run = self._calculate_next_run(frequency, cron_expression)
        
        schedule = Schedule(
            id=schedule_id,
            job_type=job_type,
            frequency=frequency,
            cron_expression=cron_expression,
            enabled=True,
            next_run=next_run
        )
        
        self._save_schedule(schedule)
        return schedule
    
    def _calculate_next_run(
        self,
        frequency: Optional[str],
        cron_expression: Optional[str]
    ) -> Optional[datetime]:
        """Calculate next run time based on frequency or cron"""
        now = datetime.utcnow()
        
        if cron_expression:
            try:
                cron = croniter(cron_expression, now)
                return cron.get_next(datetime)
            except Exception:
                return None
        
        if frequency == "hourly":
            from datetime import timedelta
            return now + timedelta(hours=1)
        elif frequency == "daily":
            from datetime import timedelta
            return now + timedelta(days=1)
        elif frequency == "weekly":
            from datetime import timedelta
            return now + timedelta(weeks=1)
        
        return None
    
    def _save_schedule(self, schedule: Schedule):
        """Save schedule to database"""
        import sqlite3
        import json
        
        db_path = self.repo.db_path
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO schedules 
                (id, job_type, frequency, cron_expression, enabled, last_run, next_run, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule.id,
                schedule.job_type,
                schedule.frequency,
                schedule.cron_expression,
                1 if schedule.enabled else 0,
                schedule.last_run.isoformat() if schedule.last_run else None,
                schedule.next_run.isoformat() if schedule.next_run else None,
                schedule.created_at.isoformat() if schedule.created_at else datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        import sqlite3
        
        db_path = self.repo.db_path
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
            if not row:
                return None
            
            return Schedule(
                id=row["id"],
                job_type=row["job_type"],
                frequency=row["frequency"],
                cron_expression=row["cron_expression"],
                enabled=bool(row["enabled"]),
                last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None,
                next_run=datetime.fromisoformat(row["next_run"]) if row["next_run"] else None,
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow(),
            )
    
    def list_schedules(self) -> List[Schedule]:
        """List all schedules"""
        import sqlite3
        
        db_path = self.repo.db_path
        schedules = []
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM schedules ORDER BY created_at DESC").fetchall()
            for row in rows:
                schedules.append(Schedule(
                    id=row["id"],
                    job_type=row["job_type"],
                    frequency=row["frequency"],
                    cron_expression=row["cron_expression"],
                    enabled=bool(row["enabled"]),
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None,
                    next_run=datetime.fromisoformat(row["next_run"]) if row["next_run"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow(),
                ))
        return schedules

