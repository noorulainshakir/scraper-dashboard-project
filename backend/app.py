import sys
import os
import uuid
import threading
import asyncio
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noco_wink_inventory_sync.nocodb_manager import NocoDBManager
from noco_wink_inventory_sync.wink_inventory_sync import WinkInventorySync
from websocket_manager import manager

app = FastAPI()

# Mount frontend (static files)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


# -------------------------------
# In-memory jobs store
# -------------------------------
JOBS = {}  # {job_id: {"status":..., "progress":..., "stats":..., "logs":[], "error":...}}

# -------------------------------
# Wink Inventory Sync API Router
# -------------------------------
router = APIRouter(prefix="/api/services/wink-sync", tags=["wink-sync"])

@router.post("/start")
def start_sync():
    job_id = "job_" + str(uuid.uuid4())[:8]
    JOBS[job_id] = {"status": "running", "progress": 0, "stats": None, "logs": [], "error": None}

    def run_sync_job():
        try:
            import time
            # Dummy loop: 15 minutes (simulate progress)
            for i in range(15):
                JOBS[job_id]["progress"] = int((i + 1) / 15 * 100)
                JOBS[job_id]["logs"].append(f"Step {i+1}: progress {JOBS[job_id]['progress']}%")
                time.sleep(60)

            JOBS[job_id]["stats"] = {"message": "Dummy sync finished successfully"}
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["progress"] = 100
            JOBS[job_id]["logs"].append("Job completed successfully.")

        except Exception as e:
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["logs"].append(f"Job failed: {str(e)}")

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
    job["logs"].append("Job stopped manually.")
    return {"job_id": job_id, "status": "stopped"}

@router.get("/logs/{job_id}")
def get_logs(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    return {"job_id": job_id, "logs": job.get("logs") or []}

@router.post("/schedule")
def schedule_sync(payload: dict):
    job_id = payload.get("job_id")
    frequency = payload.get("frequency")
    cron = payload.get("cron")

    if not job_id:
        return JSONResponse({"error": "job_id required"}, status_code=400)

    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)

    # Save schedule info
    job["schedule"] = {"frequency": frequency, "cron": cron}
    job["logs"].append(f"Job scheduled: {frequency or cron}")

    return {"job_id": job_id, "scheduled": True, "schedule": job["schedule"]}


# Register router
app.include_router(router)

# -------------------------------
# WebSocket for live logs
# -------------------------------
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(2)
            # Broadcast all jobs logs
            for job_id, job in JOBS.items():
                if job.get("logs"):
                    await websocket.send_text(f"Job {job_id}: {job['logs'][-1]}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
