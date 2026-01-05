import cv2
import threading
import time
import numpy as np
from typing import Optional, Tuple
from .health import health_service
from ..logging.logger import logger
from ..config.settings import settings

class CameraService:
    def __init__(
        self,
        name: str,
        device_path: Optional[str],
        device_index: Optional[int],
        resolution: Tuple[int, int],
        framerate: int,
        pixel_format: str,
        simulation: bool,
    ):
        self.name = name
        self.device_path = device_path
        self.device_index = device_index
        self.resolution = resolution
        self.framerate = framerate
        self.pixel_format = pixel_format
        self.simulation_mode = simulation
        
        self.cap = None
        self.frame = None
        self.stopped = False
        self.thread = None
        self.last_frame_time = 0
        self.fps = 0
        self.error = None
        self._last_state = None
        self._last_error_reported = None

    def start(self):
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True, name=f"CameraThread-{self.name}")
        self.thread.start()
        logger.log(self.name, f"Camera thread started for {self.name} targeting {self._target_label()}")

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
                self._set_state("ACTIVE", message="Simulation Mode")
                time.sleep(1 / self.framerate)  # Match target FPS
                continue

            # Real Hardware Path
            if self.cap is None or not self.cap.isOpened():
                self._connect()
                if self.cap is None:
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self._set_state("WAITING", message="Capture interrupted", error="Failed to grab frame")
                self._release_capture()
                time.sleep(1)
                continue

            self.frame = frame
            self.last_frame_time = time.time()
            self.fps = self.framerate
            self._set_state("ACTIVE")

    def _connect(self):
        target = self.device_path if self.device_path else self.device_index

        if target is None:
            self._set_state("FAULTY", message="No camera target configured", error="Camera target missing")
            return

        try:
            logger.log(
                self.name,
                f"Opening camera at {target}",
                level="INFO",
                intent="Initialize hardware capture",
                action=f"Requesting {self.pixel_format} {self.resolution[0]}x{self.resolution[1]} @ {self.framerate}fps",
            )
            
            self.cap = cv2.VideoCapture(target)
            if self.cap.isOpened():
                self._configure_capture()
                self.error = None
                self._set_state("ACTIVE", message="Camera connected")
            else:
                self.cap = None
                raise Exception(f"Camera unavailable at {target}")
        except Exception as e:
            self.error = str(e)
            self._set_state("WAITING", message="Camera unavailable", error=self.error)

    def _configure_capture(self):
        fourcc = cv2.VideoWriter_fourcc(*self.pixel_format)
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)

    def _release_capture(self):
        if self.cap:
            self.cap.release()
        self.cap = None

    def _target_label(self) -> str:
        if self.device_path:
            return self.device_path
        if self.device_index is not None:
            return f"index {self.device_index}"
        return "unconfigured"

    def _set_state(self, state: str, message: Optional[str] = None, error: Optional[str] = None):
        state_changed = state != self._last_state
        error_changed = error is not None and error != self._last_error_reported

        if state_changed:
            logger.log(
                self.name,
                f"State {self._last_state or 'INIT'} -> {state}",
                level="INFO" if state == "ACTIVE" else "WARN",
                action=message or "State change",
            )

        health_error = error if error_changed else None
        health_service.update_status(self.name, state, message=message, error=health_error)

        self._last_state = state
        if error_changed:
            self._last_error_reported = error
        self.error = error

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
            "simulation": self.simulation_mode or simulation_service.active,
            "device": self._target_label(),
            "pixel_format": self.pixel_format,
        }

camera_rear = CameraService(
    name="camera_rear", 
    device_path=settings.camera_rear.device_path,
    device_index=settings.camera_rear.device_index,
    resolution=tuple(settings.camera_rear.resolution),
    framerate=settings.camera_rear.framerate,
    pixel_format=settings.camera_rear.pixel_format,
    simulation=settings.camera_rear.simulation
)

camera_front = CameraService(
    name="camera_front",
    device_path=settings.camera_front.device_path,
    device_index=settings.camera_front.device_index,
    resolution=tuple(settings.camera_front.resolution),
    framerate=settings.camera_front.framerate,
    pixel_format=settings.camera_front.pixel_format,
    simulation=settings.camera_front.simulation
)
