from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid, threading
from noco_wink_inventory_sync.nocodb_manager import NocoDBManager
from noco_wink_inventory_sync.wink_inventory_sync import WinkInventorySync


app = FastAPI()

# Mount frontend at /frontend instead of /
app.mount("/frontend", StaticFiles(directory="backend/frontend", html=True), name="frontend")


# -------------------------------
# Wink Inventory Sync API Router
# -------------------------------
router = APIRouter(prefix="/api/services/wink-sync", tags=["wink-sync"])

# Temporary in-memory jobs store (replace with Redis later)
JOBS = {}  # {job_id: {"status": "running", "progress": 0, "stats": {}, "error": None}}

@router.post("/start")
def start_sync():
    job_id = "job_" + str(uuid.uuid4())[:8]
    JOBS[job_id] = {"status": "running", "progress": 0, "stats": None, "error": None}

    def run_sync_job():
        try:
            # Initialize NocoDB manager from environment variables
            nocodb_manager = NocoDBManager(
                api_token=os.getenv("NOCODB_API_TOKEN"),
                base_url=os.getenv("NOCODB_BASE_URL"),
                project_name=os.getenv("NOCODB_PROJECT_NAME"),
                table_name=os.getenv("NOCODB_TABLE_NAME"),
            )

            # Run Wink Inventory Sync
            sync = WinkInventorySync(nocodb_manager)
            stats = sync.sync_inventory()

            JOBS[job_id]["stats"] = stats
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["progress"] = 100
        except Exception as e:
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["status"] = "failed"

    threading.Thread(target=run_sync_job, daemon=True).start()
    return {"job_id": job_id, "status": "running"}

@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    return {"job_id": job_id, **job}

@router.post("/stop/{job_id}")
def stop_sync(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    job["status"] = "stopped"
    return {"job_id": job_id, "status": "stopped"}

@router.get("/logs/{job_id}")
def get_logs(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    return {"job_id": job_id, "logs": job.get("stats") or {}}

@router.post("/schedule")
def schedule_sync(payload: dict):
    # Stub: later integrate with Celery beat / APScheduler
    return {"scheduled": True, "details": payload}

# Register router
app.include_router(router)
