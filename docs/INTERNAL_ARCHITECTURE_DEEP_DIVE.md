# VanDash: Internal Architecture Deep Dive

This document provides a technical, exhaustive look at the internals of VanDash. It is intended for the owner to understand the system's "wiring" before performing a Raspberry Pi deployment.

---

## 1. Filesystem & Environment Model

### Python Module Paths vs. Filesystem Paths

VanDash is structured as a standard Python package.

- **Filesystem**: `backend/app/main.py`
- **Module Path**: `app.main` (when running from the `backend/` directory).
Uvicorn is instructed to run `app.main:app`. This means it looks inside the `app` folder (which contains an `__init__.py`) for a file named `main.py`, and inside that file, it looks for an object named `app`.

### WSL Drive Mapping

When developing on Windows via WSL:

- Your Windows `C:\` drive is mounted at `/mnt/c/`.
- The repository at `c:\Users\PC\Desktop\VanDash` is seen by WSL as `/mnt/c/Users/PC/Desktop/VanDash`.
- **Note**: Development inside WSL's native filesystem (e.g., `/home/user/code`) is faster, but `C:\Users\...` is used here for direct visibility between Windows (browser/editor) and the Linux environment.

### Raspberry Pi Deployment Layout

On a production Pi, the repo should reside at `/home/pi/VanDash`.

- The `systemd` service is configured to expect the `backend/` folder at this specific path.
- Python dependencies are managed by `uv` inside a virtual environment (`.venv`) localized to the project folder.

---

## 2. Configuration System

### Maintenance vs. Operational Files

VanDash uses two explicit configuration files to prevent environment confusion:

- **`config/maintenance.yaml`**: Used only on the laptop. Defaults to simulation but permits hardare probing via `allow_real`.
- **`config/operational.yaml`**: Used only on the Pi. Hardened for production with no simulation.

### Initialization & Loading

The configuration is orchestrated by `backend/app/config/settings.py`.

1. **Selection**: The system picks `maintenance.yaml` if it exists; otherwise, it requires `operational.yaml`.
2. **Intent Check**: If `simulation: true` is set, but `allow_real: true` is also present, the system will probe for hardware. If hardware exists, it **self-overrides** to use the real device. If missing, it stays in simulation. This allows "zero-config" testing of sensors on the laptop.

---

## 3. Modes of Operation

### Maintenance (Laptop Only)

- **Environment**: WSL/Windows/Mac.
- **Goal**: Code updates, UI testing, sensor discovery.
- **Networking**: Laptop usually has internet access while connected to the Pi AP.

### Operational (Pi Only)

- **Environment**: Raspberry Pi 4/5.
- **Goal**: Appliance-like stability. No Node.js or development tools are run here.
- **Networking**: Static IP 192.168.4.1. No internet assumed.

### Simulation vs. Real Hardware

Every hardware subsystem has a `simulation` flag in the YAML.

- **Simulation = True**: Services bypass `/dev/video*` or Bluetooth sockets and generate synthetic data (sine wave RPMs, moving test patterns).
- **Simulation = False**: Services attempt to open raw device descriptors. If the device is missing, the service enters the retry loop.

---

## 4. Subsystem Architecture (Threaded Isolation)

Every major hardware component runs in its own **Background Thread**. This ensures a slow OBD adapter doesn't freeze the Camera stream.

| Subsystem | Folder | Start Mechanism | Failure Detection |
| :--- | :--- | :--- | :--- |
| **Camera** | `services/camera.py` | `threading.Thread` | `cv2.VideoCapture.read()` returns `False` |
| **OBD-II** | `services/obd.py` | `threading.Thread` | `obd.is_connected()` check on every poll |
| **System** | `services/system.py` | Synchronous on API request | File descriptor errors in `/sys/class/thermal` |
| **Health** | `services/health.py` | Central Singleton | State machine: `ACTIVE -> WAITING -> FAULTY` |

### Graceful Degradation

When a failure is detected:

1. The thread logs the error to the `LoggingService`.
2. The `HealthService` increments the restart counter.
3. The service waits (`supervision.backoff_seconds`) before trying again.
4. After 3 failures, the thread stops trying and flags the UI.

---

## 5. Device Handling

### Camera Discovery (`/dev/video*`)

Linux treats USB cameras as files. The `device_index: 0` in your config corresponds to `/dev/video0`.

- **Pi Specifics**: If you have multiple USB devices, the index might shift. VanDash expects the owner to verify the index via `v4l2-ctl --list-devices` if the default fails.
- **Mismatches**: If you select an index that isn't a camera, OpenCV will throw a connection error, which surfaces in the **Diag** view with the specific hardware code.

### OBD Discovery

The OBD service uses `python-obd`. If `port` is `null`, it scans `/dev/rfcomm*` and `/dev/ttyUSB*` automatically.

---

## 6. Startup Sequence

1. **Stage 1: OS Boot**: Pi Power-on $\rightarrow$ Linux Kernel $\rightarrow$ Systemd.
2. **Stage 2: Backend Init**: `uvicorn` starts $\rightarrow$ `app.main` is imported $\rightarrow$ `settings.py` loads YAML.
3. **Stage 3: Service Init**: `startup_event()` triggers `obd_service.start()` and `camera_service.start()`. Each spawns its own thread.
4. **Stage 4: UI Readiness**: The backend starts serving index.html. The camera thread begins producing JPEG buffers.
5. **Stage 5: Live**: Browser connects $\rightarrow$ Requests `/api/obd/stream` (SSE) and `/api/camera/rear/stream` (MJPEG).

---

## 7. Observability & Debugging

### In-Browser Diagnostics

VanDash is designed so you **rarely need SSH**.

- **Logs**: A `collections.deque(maxlen=1000)` stores recent logs in RAM. These are exposed via `/api/logs/tail`.
- **Health State**: Computed dynamically. If `networking` or `backend` are `FAULTY`, the whole system is `FAULTY`. If only a sensor is down, it's `DEGRADED`.
- **Status Corner**: A React component that polls `/api/health` every 2s to show real-time "heartbeats" of every thread.

---

## 8. Failure Scenarios (How they appear)

| Scenario | Background Behavior | UI Appearance |
| :--- | :--- | :--- |
| **Missing Camera** | `CameraService` hits backoff loop | Black screen + "Camera Offline" placeholder |
| **OBD Adapter Off** | `OBDService` enters `WAITING` state | Gauges show "--" / "DISCONNECTED" text |
| **Bad Config Type** | Backend fails to start (Pydantic error) | Browser shows "Connection Refused" |
| **Max Retries Hit** | Thread terminates (suspends polling) | Red text: "MANUAL RESET REQUIRED" in Diag |

---
**End of Deep Dive.**
