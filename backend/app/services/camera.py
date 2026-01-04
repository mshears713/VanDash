import cv2
import threading
import time
import numpy as np
from typing import Optional, Tuple
from .health import health_service
from ..logging.logger import logger
from ..config.settings import settings

class CameraService:
    def __init__(self, name: str, device_index: int, resolution: Tuple[int, int], simulation: bool):
        self.name = name
        self.device_index = device_index
        self.resolution = resolution
        self.simulation_mode = simulation
        
        self.cap = None
        self.frame = None
        self.stopped = False
        self.thread = None
        self.last_frame_time = 0
        self.fps = 0
        self.error = None

    def start(self):
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True, name=f"CameraThread-{self.name}")
        self.thread.start()
        logger.log(self.name, f"Camera thread started for {self.name}")

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()

    def _update(self):
        while not self.stopped:
            from .simulation import simulation_service
            
            # Global Simulation Override
            use_sim = self.simulation_mode or simulation_service.active
            
            # Maintenance Override logic
            if not simulation_service.active and settings.mode == "maintenance" and self.simulation_mode:
                # Add allow_real check if needed, but for simplicity let's use the current pattern
                pass

            if use_sim:
                self._simulate_frame()
                health_service.update_status(self.name, "ACTIVE", message="Simulation Mode")
                time.sleep(1/30) # 30 FPS
                continue

            # Real Hardware Path
            if self.cap is None or not self.cap.isOpened():
                self._connect()
                if self.cap is None:
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.error = "Failed to grab frame"
                health_service.update_status(self.name, "WAITING", error=self.error)
                logger.log(self.name, "Capture interrupted", level="ERROR", 
                           reason="Frame buffer empty or device disconnected",
                           action="Entering retry loop")
                self.cap.release()
                self.cap = None
                continue

            self.frame = frame
            self.last_frame_time = time.time()
            health_service.update_status(self.name, "ACTIVE")
            self.fps = 30 

    def _connect(self):
        try:
            logger.log(self.name, f"Probing device index {self.device_index}", level="DEBUG",
                       intent="Initialize hardware capture", action="Opening CV2 VideoCapture")
            
            self.cap = cv2.VideoCapture(self.device_index)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                logger.log(self.name, f"Camera {self.name} connected at index {self.device_index}", level="INFO",
                           reason="Hardware handshake successful", action="Starting capture loop")
                self.error = None
            else:
                self.cap = None
                raise Exception(f"Device index {self.device_index} exists but rejected stream request")
        except Exception as e:
            self.error = str(e)
            health_service.update_status(self.name, "WAITING", error=self.error)
            logger.log(self.name, "Hardware initialization failed", level="WARN",
                       reason=str(e), action="Subsystem entering WAITING state for retry")

    def _simulate_frame(self):
        from .simulation import simulation_service
        
        # Create a test pattern with moving elements
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        t = time.time()
        
        # Moving circle - uses global simulation cycle for responsiveness
        cycle = simulation_service.get_cycle_value()
        
        if self.name == "camera_rear":
            # Rear pattern: Orbiting circle
            cx = int(320 + 200 * np.cos(t * 2))
            cy = int(240 + 150 * np.sin(t * 2))
            cv2.circle(frame, (cx, cy), 50, (0, 210, 255), -1)
            cv2.putText(frame, "REAR CAMERA SIMULATION", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            # Front pattern: Pulsing circle in center
            radius = int(50 + 100 * cycle)
            cv2.circle(frame, (320, 240), radius, (255, 100, 0), 2)
            cv2.circle(frame, (320, 240), 10, (255, 255, 255), -1)
            cv2.putText(frame, "FRONT CAMERA SIMULATION", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.putText(frame, f"TIME: {time.strftime('%H:%M:%S')}", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Add some "analog noise"
        noise = np.random.randint(0, 10, (480, 640, 3), dtype=np.uint8)
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
        from .simulation import simulation_service
        return {
            "detected": self.cap is not None or self.simulation_mode or simulation_service.active,
            "last_frame_time": self.last_frame_time,
            "fps": self.fps,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "error": self.error,
            "simulation": self.simulation_mode or simulation_service.active
        }

camera_rear = CameraService(
    name="camera_rear", 
    device_index=settings.camera_rear.device_index,
    resolution=tuple(settings.camera_rear.resolution),
    simulation=settings.camera_rear.simulation
)

camera_front = CameraService(
    name="camera_front",
    device_index=settings.camera_front.device_index,
    resolution=tuple(settings.camera_front.resolution),
    simulation=settings.camera_front.simulation
)
