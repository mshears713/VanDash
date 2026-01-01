import logging
from datetime import datetime
from collections import deque
from typing import List, Dict, Optional

class LogEntry:
    def __init__(self, source: str, level: str, message: str):
        self.timestamp = datetime.now().isoformat()
        self.source = source
        self.level = level
        self.message = message
from typing import List, Dict, Optional, Any
from ..config.settings import settings

class LoggingService:
    def __init__(self, max_logs: int = 1000):
        self.logs = deque(maxlen=max_logs)
        self.sources = set()

    def log(self, source: str, message: str, level: str = "INFO", intent: Optional[str] = None, reason: Optional[str] = None, action: Optional[str] = None):
        source = source.upper()
        self.sources.add(source)
        
        timestamp = datetime.now().isoformat()
        
        # Narrative construction
        full_message = message
        if intent:
            full_message = f"Intent: {intent} | {full_message}"
        if reason:
            full_message = f"{full_message} | Reason: {reason}"
        if action:
            full_message = f"{full_message} | Action: {action}"
            
        log_entry = {
            "timestamp": timestamp,
            "source": source,
            "level": level,
            "message": full_message
        }
        
        # Verbosity control
        # In operational mode, we suppress non-essential INFO if needed, 
        # but for now we follow the 'concise vs verbose' rule.
        is_maintenance = settings.mode == "maintenance"
        
        if level == "DEBUG" and not is_maintenance:
            return

        self.logs.append(log_entry)
        
        # Console output for dev
        print(f"[{timestamp}] {source} {level}: {full_message}")

    def get_sources(self) -> List[str]:
        return sorted(list(self.sources))

    def tail(self, source: Optional[str] = None, lines: int = 50, level: Optional[str] = None) -> List[Dict[str, Any]]:
        filtered = list(self.logs)
        if source:
            filtered = [l for l in filtered if l["source"] == source.upper()]
        if level:
            filtered = [l for l in filtered if l["level"] == level.upper()]
            
        return filtered[-lines:]

logger = LoggingService()

# Environment Warnings (Non-fatal)
if settings.mode == "maintenance":
    if settings.is_wsl:
        logger.log("SYSTEM", "Environment: Running under WSL", level="INFO", 
                   reason="WSL environment detected", 
                   action="Informative only - note that USB access differs from native Linux")
    if settings.is_mounted:
        logger.log("SYSTEM", "Filesystem: Repo located under /mnt/*", level="WARN", 
                   reason="Windows-mounted drives under WSL can be slow", 
                   action="File watching may be unreliable. Consider moving to WSL native home if speed is an issue.")
