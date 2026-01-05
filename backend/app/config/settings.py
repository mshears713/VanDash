import yaml
import os
import platform
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class NetworkConfig(BaseModel):
    ssid: str
    password: str
    fixed_ip: str

class BackendConfig(BaseModel):
    port: int
    log_level: str

class CameraConfig(BaseModel):
    device_path: Optional[str] = None
    device_index: Optional[int] = None
    resolution: List[int] = [720, 480]
    framerate: int = 30
    pixel_format: str = "MJPG"
    simulation: bool = True
    allow_real: bool = False

class OBDConfig(BaseModel):
    port: Optional[str] = None
    simulation: bool = True
    allow_real: bool = False
    polling_interval: float = 0.5

class SupervisionConfig(BaseModel):
    max_retries: int = 3
    backoff_seconds: float = 5.0

class Settings(BaseModel):
    mode: str = "operational" # "maintenance" | "operational"
    network: NetworkConfig
    backend: BackendConfig
    camera_rear: CameraConfig
    camera_front: CameraConfig
    obd: OBDConfig
    supervision: SupervisionConfig
    
    # Environment info
    is_wsl: bool = False
    is_mounted: bool = False

    @validator("mode")
    def validate_mode(cls, v):
        if v not in ["maintenance", "operational"]:
            raise ValueError("Mode must be 'maintenance' or 'operational'")
        return v

def detect_environment():
    is_wsl = "microsoft-standard" in platform.release().lower()
    is_mounted = False
    
    if is_wsl:
        # Check if running under /mnt/
        cwd = os.getcwd()
        if cwd.startswith("/mnt/"):
            is_mounted = True
            
    return is_wsl, is_mounted

def load_settings() -> Settings:
    # Config selection order:
    # 1. VANDASH_CONFIG (explicit path)
    # 2. VANDASH_PROFILE=operational|maintenance (default operational)
    # 3. Fallback to operational.yaml, then maintenance.yaml if present

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    
    op_path = os.path.join(base_dir, "config/operational.yaml")
    maint_path = os.path.join(base_dir, "config/maintenance.yaml")
    
    config_file = None

    explicit_path = os.getenv("VANDASH_CONFIG")
    if explicit_path:
        if not os.path.exists(explicit_path):
            raise FileNotFoundError(f"VANDASH_CONFIG set to {explicit_path}, but file does not exist")
        config_file = explicit_path
    else:
        profile = os.getenv("VANDASH_PROFILE", "operational").lower()
        if profile == "maintenance" and os.path.exists(maint_path):
            config_file = maint_path
        elif os.path.exists(op_path):
            config_file = op_path
        elif os.path.exists(maint_path):
            config_file = maint_path
    
    if not config_file:
        raise FileNotFoundError("No configuration file found in config/ (maintenance.yaml or operational.yaml)")
    
    try:
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
            settings = Settings(**data)
            
            is_wsl, is_mounted = detect_environment()
            settings.is_wsl = is_wsl
            settings.is_mounted = is_mounted
            
            return settings
    except Exception as e:
        print(f"CRITICAL: Failed to load config from {config_file}: {e}")
        raise

settings = load_settings()
