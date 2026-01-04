import time
from typing import Dict, Any

class SimulationService:
    def __init__(self):
        self.active = False
        self.start_time = 0
        self.cycle_duration = 15.0 # Seconds

    def toggle(self) -> bool:
        self.active = not self.active
        if self.active:
            self.start_time = time.time()
        return self.active

    def get_cycle_value(self) -> float:
        """Returns a value from 0 to 1 back to 0 over cycle_duration."""
        if not self.active:
            return 0.5 # Default middle value
        
        elapsed = time.time() - self.start_time
        phase = (elapsed % self.cycle_duration) / self.cycle_duration
        # Triangle wave: 0 -> 1 -> 0
        triangle = 1.0 - abs(2.0 * phase - 1.0)
        return triangle

simulation_service = SimulationService()
