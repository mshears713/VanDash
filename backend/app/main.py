from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional
import time
import os

app = FastAPI(title="VanDash API")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SubsystemStatus(BaseModel):
    state: str  # ACTIVE | WAITING | FAULTY | DISABLED
    message: Optional[str] = None
    last_update: float
    restart_count: int = 0

class HealthResponse(BaseModel):
    status: str  # OK | DEGRADED | FAULTY
    subsystems: Dict[str, SubsystemStatus]
    timestamp: float

from .services.health import health_service
from .services.system import system_service
from .services.obd import obd_service
from .services.camera import camera_rear, camera_front
from .services.simulation import simulation_service
from .logging.logger import logger as dash_logger
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.on_event("startup")
async def startup_event():
    obd_service.start()
    camera_rear.start()
    camera_front.start()
    dash_logger.log("backend", "VanDash Backend started")

@app.get("/api/camera/rear/status")
async def get_camera_rear_status():
    return camera_rear.get_status()

@app.get("/api/camera/front/status")
async def get_camera_front_status():
    return camera_front.get_status()

@app.get("/api/camera/rear/stream")
async def get_camera_rear_stream():
    def frame_generator():
        while True:
            frame = camera_rear.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/camera/front/stream")
async def get_camera_front_stream():
    def frame_generator():
        while True:
            frame = camera_front.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.1)
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/api/system/simulation/toggle")
async def toggle_simulation():
    is_active = simulation_service.toggle()
    dash_logger.log("SYSTEM", f"Simulation mode {'ENABLED' if is_active else 'DISABLED'}", 
                   level="INFO", action="Toggling global simulation state")
    return {"active": is_active}

@app.get("/api/health")
async def get_health():
    return health_service.get_health_summary()

@app.get("/api/status")
async def get_status():
    stats = system_service.get_stats()
    stats["mode"] = "operational"
    return stats

@app.get("/api/logs/sources")
async def get_log_sources():
    return dash_logger.get_sources()

@app.get("/api/logs/tail")
async def tail_logs(source: Optional[str] = None, lines: int = 50, level: Optional[str] = None):
    return dash_logger.tail(source, lines, level)

@app.get("/api/system/telemetry")
async def get_system_telemetry():
    return system_service.get_telemetry()

@app.post("/api/system/reset/{subsystem}")
async def reset_subsystem(subsystem: str):
    health_service.reset_subsystem(subsystem)
    return {"status": "reset_triggered", "subsystem": subsystem}

@app.get("/api/obd/latest")
async def get_obd_latest():
    return obd_service.get_latest()

@app.get("/api/obd/stream")
async def stream_obd_data():
    async def event_generator():
        while True:
            data = obd_service.get_latest()
            if data:
                yield {
                    "data": json.dumps(data)
                }
            await asyncio.sleep(0.5) # 2Hz stream
            
    return EventSourceResponse(event_generator())

@app.get("/api/test/fail")
async def simulate_failure(subsystem: str = "obd"):
    health_service.update_status(subsystem, "FAULTY", error="Simulated hardware failure", message="Hardware not responding")
    return {"message": f"Simulated failure in {subsystem}"}

# Serve frontend build output
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    async def root_fallback():
        return {"message": "VanDash Backend running. Frontend dist not found. Run npm build in frontend."}
