import cv2
import threading
import time
import numpy as np
from typing import Optional
from .health import health_service
from ..logging.logger import logger
from ..config.settings import settings

class CameraService:
    def __init__(self):
        self.device_index = settings.camera_rear.device_index
        self.cap = None
        self.frame = None
        self.stopped = False
        self.thread = None
        self.last_frame_time = 0
        self.fps = 0
        self.resolution = tuple(settings.camera_rear.resolution)
        self.error = None
        self.simulation_mode = settings.camera_rear.simulation

    def start(self):
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logger.log("camera_rear", "Camera thread started")

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()

    def _update(self):
        while not self.stopped:
            # Intent Check: Should we use simulation?
            use_sim = self.simulation_mode
            
            # Maintenance Override: If allowed real hardware, attempt to find it first
            if settings.mode == "maintenance" and settings.camera_rear.simulation and settings.camera_rear.allow_real:
                # We check if anything is likely there before switching
                temp_cap = cv2.VideoCapture(self.device_index)
                if temp_cap.isOpened():
                    logger.log("CAMERA_REAR", f"Maintenance mode: Real hardware detected at index {self.device_index}.", level="INFO",
                               reason="allow_real is True and device is available",
                               action="Self-overriding simulation to use real hardware")
                    use_sim = False
                    temp_cap.release()
                else:
                    logger.log("CAMERA_REAR", f"Maintenance mode: No hardware at index {self.device_index}.", level="DEBUG",
                               reason="allow_real is True but device is unavailable",
                               action="Staying in simulation mode")

            if use_sim:
                self._simulate_frame()
                health_service.update_status("camera_rear", "ACTIVE", message="Simulation Mode")
                time.sleep(1/30) # 30 FPS
                continue

            # Real Hardware Path
            if self.cap is None or not self.cap.isOpened():
                self._connect()
                if self.cap is None:
                    # In maintenance mode, we might want to fall back to simulation if real fails
                    if settings.mode == "maintenance":
                         logger.log("CAMERA_REAR", "Hardware connection failed. Falling back to simulation.", level="WARN",
                                   reason="Hardware init failed", action="Using test pattern and resetting health state")
                         self.simulation_mode = True # Temporary override
                         health_service.reset_subsystem("camera_rear")
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.error = "Failed to grab frame"
                health_service.update_status("camera_rear", "WAITING", error=self.error)
                logger.log("CAMERA_REAR", "Capture interrupted", level="ERROR", 
                           reason="Frame buffer empty or device disconnected",
                           action="Entering retry loop")
                self.cap.release()
                self.cap = None
                continue

            self.frame = frame
            self.last_frame_time = time.time()
            health_service.update_status("camera_rear", "ACTIVE")
            self.fps = 30 

    def _connect(self):
        try:
            logger.log("CAMERA_REAR", f"Probing device index {self.device_index}", level="DEBUG",
                       intent="Initialize hardware capture", action="Opening CV2 VideoCapture")
            
            self.cap = cv2.VideoCapture(self.device_index)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                logger.log("CAMERA_REAR", f"Camera connected at index {self.device_index}", level="INFO",
                           reason="Hardware handshake successful", action="Starting capture loop")
                self.error = None
            else:
                self.cap = None
                raise Exception(f"Device index {self.device_index} exists but rejected stream request")
        except Exception as e:
            self.error = str(e)
            health_service.update_status("camera_rear", "WAITING", error=self.error)
            logger.log("CAMERA_REAR", "Hardware initialization failed", level="WARN",
                       reason=str(e), action="Subsystem entering WAITING state for retry")

    def _simulate_frame(self):
        # Create a test pattern with moving elements to show it's live
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        t = time.time()
        
        # Moving circle
        cx = int(320 + 200 * np.cos(t * 2))
        cy = int(240 + 150 * np.sin(t * 2))
        cv2.circle(frame, (cx, cy), 50, (0, 210, 255), -1)
        
        # Static text
        cv2.putText(frame, "REAR CAMERA SIMULATION", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"TIME: {time.strftime('%H:%M:%S')}", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Add some "analog noise"
        noise = np.random.randint(0, 20, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        self.frame = frame
        self.last_frame_time = t

    def get_frame(self):
        if self.frame is None:
            return None
        ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            return None
        return jpeg.tobytes()

    def get_status(self):
        return {
            "detected": self.cap is not None or self.simulation_mode,
            "last_frame_time": self.last_frame_time,
            "fps": self.fps,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "error": self.error,
            "simulation": self.simulation_mode
        }

camera_service = CameraService()
