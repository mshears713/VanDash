import psutil
import time

class SystemService:
    def __init__(self):
        self.start_time = time.time()

    def get_stats(self):
        try:
            # CPU Temperature (Raspberry Pi specific)
            cpu_temp = 0.0
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = float(f.read()) / 1000.0
            except FileNotFoundError:
                # Fallback for non-Pi systems (development)
                cpu_temp = 45.0 + (time.time() % 10) 

            return {
                "cpu_temp": round(cpu_temp, 1),
                "cpu_usage": psutil.cpu_percent(),
                "ram_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": int(time.time() - self.start_time),
            }
        except Exception as e:
            return {"error": str(e)}

system_service = SystemService()
