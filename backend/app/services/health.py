from pydantic import BaseModel
from typing import Dict, Optional, List
import time
from ..logging.logger import logger

class SubsystemStatus(BaseModel):
    state: str  # ACTIVE | WAITING | FAULTY | DISABLED
    message: Optional[str] = None
    last_update: float
    restart_count: int = 0
    last_error: Optional[str] = None

class HealthService:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.subsystems: Dict[str, SubsystemStatus] = {
            "networking": SubsystemStatus(state="ACTIVE", last_update=time.time()),
            "backend": SubsystemStatus(state="ACTIVE", last_update=time.time()),
            "camera_rear": SubsystemStatus(state="WAITING", last_update=time.time()),
            "camera_front": SubsystemStatus(state="DISABLED", last_update=time.time()),
            "obd": SubsystemStatus(state="WAITING", last_update=time.time()),
            "logging": SubsystemStatus(state="ACTIVE", last_update=time.time()),
            "system": SubsystemStatus(state="ACTIVE", last_update=time.time()),
        }

    def update_status(self, name: str, state: str, message: Optional[str] = None, error: Optional[str] = None):
        if name not in self.subsystems:
            return

        sub = self.subsystems[name]
        
        # Supervision Check
        # We allow transitioning to ACTIVE even if at max_retries, 
        # as it signifies a successful self-healing/recovery.
        if sub.restart_count >= self.max_retries and state not in ["FAULTY", "ACTIVE"]:
            logger.log("SUPERVISOR", f"Transition to {state} blocked for {name.upper()}", level="WARN",
                       reason=f"Subsystem exceeded max retries ({self.max_retries})",
                       action="Maintaining FAULTY state until manual intervention or successful ACTIVE heartbeats")
            return

        old_state = sub.state
        sub.state = state
        sub.message = message
        sub.last_update = time.time()
        
        if error:
            sub.last_error = error
            sub.restart_count += 1
            
            logger.log(name, f"Subsystem failure detected", level="ERROR",
                       reason=error, 
                       action=f"Incrementing restart count ({sub.restart_count}/{self.max_retries})")
            
            if sub.restart_count >= self.max_retries:
                sub.state = "FAULTY"
                sub.message = "MAX RETRIES EXCEEDED. Supervision stopped."
                logger.log("SUPERVISOR", f"Subsystem {name.upper()} marked as FAULTY", level="CRITICAL",
                           reason="Hard failure threshold reached", 
                           action="Automatic recovery attempts suspended")
        else:
            if state == "ACTIVE":
                if sub.restart_count > 0:
                    logger.log(name, f"Subsystem recovered", level="INFO",
                               reason="Steady state reached", action="Resetting restart counter")
                    sub.restart_count = 0
                
                if old_state != "ACTIVE":
                    logger.log(name, f"Subsystem reached steady state (ACTIVE)", level="INFO",
                               reason="Health checks passed", action="Monitoring operational data")

    def should_retry(self, name: str) -> bool:
        if name not in self.subsystems:
            return False
        return self.subsystems[name].restart_count < self.max_retries

    def reset_subsystem(self, name: str):
        if name in self.subsystems:
            sub = self.subsystems[name]
            sub.restart_count = 0
            sub.state = "WAITING"
            sub.message = "Manual reset triggered."
            sub.last_error = None
            logger.log("SUPERVISOR", f"Manual reset triggered for {name.upper()}", level="INFO",
                       action="Resetting restart counter and state to WAITING")

    def get_health_summary(self):
        is_faulty = any(s.state == "FAULTY" for name, s in self.subsystems.items() if name in ["backend", "networking"])
        is_degraded = any(s.state == "FAULTY" for s in self.subsystems.values())
        
        status = "OK"
        if is_faulty:
            status = "FAULTY"
        elif is_degraded:
            status = "DEGRADED"
            
        return {
            "status": status,
            "subsystems": self.subsystems,
            "timestamp": time.time()
        }

from ..config.settings import settings
health_service = HealthService(max_retries=settings.supervision.max_retries)
