import obd
import time
import threading
from typing import Dict, Any, Optional
from .health import health_service
from ..logging.logger import logger
from ..config.settings import settings

class OBDService:
    def __init__(self):
        self.port = settings.obd.port
        self.connection = None
        self.latest_data: Dict[str, Any] = {}
        self.is_running = False
        self.thread = None
        # Use settings for retry/backoff
        self.backoff_time = settings.supervision.backoff_seconds
        self.simulation_mode = settings.obd.simulation
        self.polling_interval = settings.obd.polling_interval

        # PIDs to poll
        self.commands = [
            obd.commands.RPM,
            obd.commands.SPEED,
            obd.commands.COOLANT_TEMP,
            obd.commands.THROTTLE_POS,
            obd.commands.INTAKE_TEMP,
            obd.commands.ELM_VOLTAGE
        ]

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.thread.start()
            logger.log("obd", "OBD polling thread started")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _poll_loop(self):
        while self.is_running:
            # Intent Check: Should we use simulation?
            use_sim = self.simulation_mode
            
            # Maintenance Override
            if settings.mode == "maintenance" and settings.obd.simulation and settings.obd.allow_real:
                # We check for serial ports
                import obd
                ports = obd.scan_serial()
                if ports:
                    logger.log("OBD", f"Maintenance mode: Adapter ports detected: {ports}", level="INFO",
                               reason="allow_real is True and ports available",
                               action="Self-overriding simulation to use real hardware")
                    use_sim = False
                else:
                    logger.log("OBD", "Maintenance mode: No adapter ports found.", level="DEBUG",
                               reason="allow_real is True but no serial devices detected",
                               action="Staying in simulation mode")

            if self.connection and self.connection.is_connected():
                health_service.update_status("obd", "ACTIVE")
                self._poll_data()
            elif use_sim:
                health_service.update_status("obd", "ACTIVE", message="Simulation Mode")
                self._simulate_data()
            else:
                if not self.connection:
                    self._connect()
                else:
                    self._handle_disconnect()
            
            time.sleep(self.polling_interval)

    def _connect(self):
        try:
            logger.log("OBD", f"Probing OBD adapter on port {self.port or 'auto-scan'}", level="DEBUG",
                       intent="Establish serial handshake", action="Calling obd.OBD()")
            
            self.connection = obd.OBD(self.port)
            if self.connection.is_connected():
                logger.log("OBD", "OBD adapter connected successfully", level="INFO",
                           reason="Serial handshake confirmed", action="Entering poll loop")
            else:
                raise Exception("Adapter present but link-layer failed (Is ignition on?)")
        except Exception as e:
            logger.log("OBD", "Connection failed", level="WARN", 
                       reason=str(e), action="Subsystem entering WAITING state for backoff")
            self.connection = None
            self._handle_disconnect(error=str(e))

    def _handle_disconnect(self, error: str = "Disconnected"):
        health_service.update_status("obd", "WAITING", error=error)
        sleep_time = min(30, self.backoff_time * (health_service.subsystems["obd"].restart_count + 1))
        logger.log("OBD", f"Adapter unavailable. Retrying in {sleep_time}s", level="DEBUG",
                   reason="Not connected to vehicle ECU", action="Applying exponential backoff")
        time.sleep(sleep_time)

    def _poll_data(self):
        data = {}
        for cmd in self.commands:
            response = self.connection.query(cmd)
            if not response.is_null():
                # Convert pint quantities to serializable types
                val = response.value
                if hasattr(val, 'magnitude'):
                    data[cmd.name] = round(float(val.magnitude), 2)
                    data[f"{cmd.name}_unit"] = str(val.units)
                else:
                    data[cmd.name] = val
        
        if data:
            data["timestamp"] = time.time()
            self.latest_data.update(data)

    def _simulate_data(self):
        # Simulate some values
        import random
        t = time.time()
        self.latest_data = {
            "RPM": round(800 + 200 * (t % 10) + random.uniform(-10, 10), 0),
            "SPEED": round(40 + 5 * (t % 20) + random.uniform(-2, 2), 1),
            "COOLANT_TEMP": round(90 + random.uniform(-0.5, 0.5), 1),
            "THROTTLE_POS": round(15 + 10 * (t % 5), 1),
            "INTAKE_TEMP": 25.0,
            "ELM_VOLTAGE": 13.8,
            "timestamp": t,
            "simulated": True
        }

    def get_latest(self):
        return self.latest_data

obd_service = OBDService()
