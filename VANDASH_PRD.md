# PRD — VanDash (Raspberry Pi Vehicle Dashboard, Offline‑First)

**Doc status:** Draft v1.0 (2026‑01‑01)  
**Owner/Builder:** Mike (solo builder)  
**Primary objective:** A Raspberry‑Pi “vehicle dashboard hub” that serves a **mobile‑first** web UI to an **Android phone** over the Pi’s own Wi‑Fi network (offline by default), providing **rear camera view (analog RCA via USB capture)**, vehicle telemetry via **OBD‑II Bluetooth**, and **first‑class diagnostics**.

---

## 1) Executive Summary

VanDash is a headless Raspberry Pi system installed in a vehicle. On boot, it brings up a **local Wi‑Fi access point** and a **local web server**. The Android phone connects to the Pi’s Wi‑Fi, opens a browser to a **fixed IP address**, and sees a dashboard with:

- **Rear camera feed** (near-live; low latency)
- **(Future) Front camera feed** (placeholder in v1; architecture ready)
- **OBD-II telemetry** via Bluetooth adapter (with graceful degradation)
- **System health, service status, and logs** directly in the web UI
- **Development Environment**: Laptop (WSL/Windows) with `uv` (Python) and `npm` (React).
- **Production Environment**: Raspberry Pi (Appliance mode). No Node.js.
- **Deployment Strategy**:
    1. Develop and test in **Maintenance Mode** on the laptop.
    2. Build frontend assets on the laptop.
    3. Sync to Pi over the local Access Point (192.168.4.1) using `rsync`.
    4. Pi runs the backend service via `systemd`.

### 5.2. Network Constraints

- **SSID**: `VanDash-Hub` (Hostapd on Pi).
- **IP**: `192.168.4.1` (Static).
- **No Internet Assumption**: All updates are pushed *to* the Pi, never pulled *by* the Pi from the internet.

The system must be resilient: if one module fails, the rest keeps running and the UI explains exactly what is broken and how to diagnose it—**without requiring SSH for most issues**.

---

## 2) Goals

### 2.1 Primary goals (v1)

1. **Offline‑first AP mode:** The Pi is the Wi‑Fi access point in normal operation.
2. **Predictable addressing:** Dashboard always reachable at **fixed IP**:  
   **`http://192.168.4.1/`**
3. **Rear camera near‑live:** Rear stream optimized for low latency for reverse/parking.
4. **Telemetry + health:** OBD‑II values + subsystem health status always visible.
5. **No silent failure:** Every module reports ACTIVE / WAITING / FAULTY / DISABLED; UI shows actionable errors.
6. **Headless + auto start:** Boots and runs without keyboard/screen.

### 2.2 Secondary goals (v1)

- **Maintenance mode:** Temporarily connect Pi to iPhone hotspot to pull updates. During maintenance mode, **Android UI is allowed to be offline/unavailable**.
- **Developer workflow:** Build/test on laptop in **WSL**, deploy to Pi; use **`uv`** for Python dependency management.

---

## 3) Non‑Goals (v1)

- No cloud services required for core functionality.
- No internet‑reachable dashboard by default.
- No native Android app (browser UI only).
- No advanced driver assistance (object detection, lane assist, etc.).
- No “always‑on” simultaneous internet + AP routing in v1 (possible future).

---

## 4) Target Users & Key Use Cases

### Primary user

- One builder/operator in a van environment; intermittent internet; wants reliability and debuggability.

### Use cases

1. **Normal drive:** Android connects to Pi Wi‑Fi → opens `192.168.4.1` → sees camera + telemetry.
2. **Reverse/parking:** Rear camera view dominates; minimal UI; low latency.
3. **Partial failure:** Camera/OBD breaks → UI shows placeholder + error details; other modules continue.
4. **Maintenance/update:** Builder switches Pi to iPhone hotspot → pulls repo/builds → returns to AP mode.

---

## 5) System Context & Constraints

- Raspberry Pi (4/5 recommended) with Wi‑Fi capable of AP mode.
- Rear camera is **analog RCA**, captured via **USB video capture device**.
- Front camera is **not decided yet**; must be an optional module in architecture.
- OBD‑II via **Bluetooth adapter** (ELM327‑class variants common; variable quality).
- Power environment is vehicle-grade (noisy, potential abrupt shutdown). v1 should be tolerant and recover cleanly.

---

## 6) High‑Level Architecture

### 6.1 Components

- **Pi / Hub**
  - Wi‑Fi Access Point (offline)
  - Backend server (FastAPI)
  - Camera ingestion + streaming
  - OBD polling + caching
  - System health + logs

- **Android / Client**
  - Mobile browser
  - React SPA served from Pi

### 6.2 Data flows

- Camera frames → camera service → stream endpoint → browser player
- OBD polling loop → cache/store → API → UI (polling or push)
- Subsystem health + logs → API → diagnostics UI

---

## 7) Functional Requirements

### 7.1 Networking (AP, fixed IP)

**NET‑1:** Pi MUST boot into Access Point mode by default.  
**NET‑2:** Dashboard MUST be reachable at `http://192.168.4.1/` (fixed IP).  
**NET‑3:** AP MUST start automatically on boot (headless).  
**NET‑4:** If AP fails, system MUST mark networking subsystem FAULTY and surface details via logs (viewable once connected by alternate method).  
**NET‑5:** Maintenance mode MAY disable AP and join iPhone hotspot; while in maintenance mode, Android dashboard availability is NOT required.

**Notes:** v1 intentionally avoids “AP + internet uplink routing” complexity.

---

### 7.2 Backend (FastAPI)

**API‑1:** Backend MUST provide the following endpoints:

- `GET /api/health`  
  Returns overall status and subsystem statuses.
- `GET /api/status`  
  Returns CPU temp, RAM, disk, uptime, restart counters, current mode.
- `GET /api/logs/sources`  
  Lists available log streams (backend/camera/obd/system).
- `GET /api/logs/tail?source=...&lines=...&level=...`  
  Returns last N lines; supports basic filtering.
- `GET /api/obd/latest`  
  Returns current/last-known telemetry snapshot with timestamp and freshness.
- `GET /api/obd/stream`  
  Push updates via SSE or WebSocket (agent chooses; must be stable on mobile).
- `GET /api/camera/rear/status`
- `GET /api/camera/rear/stream`
- `GET /api/camera/front/status` (placeholder in v1)
- `GET /api/camera/front/stream` (placeholder in v1; can return “disabled”)

**API‑2:** Backend MUST serve the frontend build output:

- `GET /` returns SPA index
- static assets served from `/assets/...` (or equivalent)

**API‑3:** Backend MUST remain alive if any subsystem fails. Subsystems must be isolated.

---

### 7.3 Subsystem Health Model

**HEALTH‑1:** Each subsystem reports: `ACTIVE | WAITING | FAULTY | DISABLED`  
Subsystems:

- `networking`
- `backend`
- `camera_rear`
- `camera_front`
- `obd`
- `logging`
- `system` (temps, uptime, storage)

**HEALTH‑2:** Overall system status derived from subsystems:

- `OK` if all required subsystems ACTIVE (backend + networking) and others not FAULTY
- `DEGRADED` if backend/networking OK but at least one feature subsystem FAULTY
- `FAULTY` if backend cannot serve UI or networking prevents access

**HEALTH‑3:** UI MUST always show “Status Corner” widget with overall + key subsystem icons.

---

### 7.4 Diagnostics & Observability (Web‑first debugging)

**DIAG‑1:** UI MUST provide a Diagnostics view showing:

- subsystem checklist with states
- last error message per subsystem
- restart attempt counters
- “what to try next” suggestions (short, actionable)

**DIAG‑2:** Logs MUST be readable in the UI with:

- source selection
- tail size (e.g., 50/200/1000 lines)
- level filter (INFO/WARN/ERROR)

**DIAG‑3:** No silent failures: errors must be visible without SSH in common cases.

---

### 7.5 Rear Camera (Analog RCA via USB capture)

**CAM‑R‑1:** System MUST ingest rear camera via USB capture device (UVC / v4l2 typical).  
**CAM‑R‑2:** Stream MUST be usable in reverse/parking; latency prioritized.

#### Latency targets (v1)

- **Soft target:** median end‑to‑end latency ≤ **250 ms** on local Wi‑Fi.
- **Hard requirement:** must feel “near live” (no multi‑second lag).
- If MJPEG cannot meet this on target hardware, agents must propose/implement WebRTC for rear cam (see Risk Mitigation).

**CAM‑R‑3:** If rear camera fails, UI MUST show “Camera Offline” placeholder with last error and timestamp.

**CAM‑R‑4:** Provide `/api/camera/rear/status` including:

- device detected (yes/no)
- last frame time
- fps estimate
- resolution
- current pipeline mode (MJPEG/WebRTC/etc.)
- last error

---

### 7.6 Front Camera (Placeholder in v1)

**CAM‑F‑1:** Front camera module is optional. In v1 it may be DISABLED but must exist in the health model and UI.  
**CAM‑F‑2:** UI shows placeholder card and state, not a broken element.

---

### 7.7 OBD‑II Telemetry (Bluetooth)

**OBD‑1:** Pi connects to Bluetooth OBD adapter and polls PIDs.  
**OBD‑2:** Must tolerate disconnects and missing PIDs.  
**OBD‑3:** Must not crash backend; on repeated failures mark FAULTY and stop thrashing.  
**OBD‑4:** Cache last-known-good values and show timestamp + freshness.
**OBD‑5:** Provide retry with backoff and visible attempt counter.

Suggested initial PIDs (best-effort; not all cars support all):

- speed
- RPM
- coolant temp
- throttle position
- intake air temp
- battery voltage (if available)

---

### 7.8 Mode: Operational vs Maintenance

**MODE‑1:** Default is **Operational** (AP + dashboard).  
**MODE‑2:** Maintenance mode is explicitly activated (implementation can be config file, CLI script, or UI control).  
**MODE‑3:** In Maintenance mode, Android dashboard may be unavailable; this is acceptable for v1.  
**MODE‑4:** UI must show current mode when reachable.

---

## 8) Non‑Functional Requirements

### Reliability

- Backend must survive long sessions without crashing.
- Subsystem failures must not cascade.

### Performance

- UI responsive on Android.
- Rear camera latency prioritized over image quality in v1.
- Telemetry update rate: target 2–5 Hz (adjustable).

### Security (local-first)

- No internet exposure by default.
- No secrets committed to repo.
- Logs must not leak credentials or tokens.

### Maintainability

- Clear module boundaries: routers/services
- Good “runbook” for debugging without SSH
- Minimal dependencies (justify additions)

---

## 9) Development Workflow & Tooling (WSL + uv)

### Mandatory tooling requirements

**DEV‑1:** Python dependency management MUST use **`uv`** (not pip/poetry/conda).  
**DEV‑2:** Primary development runs in **WSL** (Linux).  
**DEV‑3:** Frontend uses Node tooling (npm/pnpm) — agent may choose but must document.

### Local dev expectations (agent to implement)

- `backend/` should run locally in WSL
- `frontend/` dev server for iteration; production build served by backend
- Provide a one‑command “smoke check” flow

---

## 10) Repository Structure (required)

```

backend/
  app/
    main.py
    routers/
    services/
    models/
    config/
    logging/
frontend/
  src/
  public/
docs/
  PRD.md
  ARCHITECTURE.md
  RUNBOOK.md
scripts/
config/
  example.yaml
  example.env

```

---

## 11) Configuration

Configuration must be explicit and centralized (YAML/TOML/ENV acceptable). Must include:

- `mode`: operational/maintenance
- `network`: ssid, password, fixed ip/cidr
- `backend`: port, log level
- `camera_rear`: device path or discovery rules, preferred resolution/fps, pipeline options
- `camera_front`: enabled flag (default false in v1)
- `obd`: adapter id/mac/name, polling interval, enabled pids
- `supervision`: retry limits, backoff timings

---

## 12) Acceptance Criteria (v1)

A build is “v1 accepted” when:

1. Pi boots headless; backend starts automatically (systemd).
2. Pi AP starts; Android connects; opening `http://192.168.4.1/` loads UI.
3. `/api/health` returns proper structure and subsystem states.
4. UI shows:
   - Drive view
   - Reverse view (rear cam primary)
   - Diagnostics view (checklist + logs)
5. Rear camera:
   - Shows live stream
   - If capture device unplugged, UI shows “Camera Offline” placeholder
6. OBD:
   - If adapter missing/disconnected, system degrades without crash
   - UI shows OBD FAULTY with retries and last-known values
7. Logs viewable from browser for backend + camera + obd sources.
8. Status corner widget always visible and accurate.

---

## 13) Milestones (agent execution plan)

### M0 — Repo scaffolding + contracts

- Create repo structure
- FastAPI skeleton + `/api/health`
- React SPA skeleton + status widget
- Backend serves built frontend

### M1 — Observability core

- Subsystem state model + `/api/status`
- Structured logging + `/api/logs/*`
- Diagnostics view (checklist + log tail)

### M2 — OBD v1

- OBD service loop + caching
- `/api/obd/latest` + stream (SSE/WebSocket)
- Telemetry UI module with failure states

### M3 — Rear camera v1 (RCA capture)

- Detect USB capture device
- Implement streaming endpoint + status endpoint
- Reverse view integrates stream + placeholder on failure
- Latency measurement notes + configuration knobs

### M4 — Supervision + restart policy

- Per-subsystem restart attempts (max 3 default)
- Degraded mode after repeated failure
- UI shows restart counters + last errors

### M5 — Pi deployment + runbook

- systemd units for backend + supporting services
- config templates
- `docs/RUNBOOK.md` for web-first debugging
- `docs/ARCHITECTURE.md` 1-page topology

---

## 14) Risks & Mitigations

### R1: Rear camera latency too high over MJPEG

- Mitigation: tune capture resolution/fps; reduce buffering; choose efficient pipeline.
- Escalation: implement WebRTC for rear camera if MJPEG cannot meet near-live requirement.

### R2: USB capture device compatibility (v4l2 quirks)

- Mitigation: abstract device detection; expose status + errors; document known-good devices if discovered.

### R3: Bluetooth OBD reliability varies

- Mitigation: robust retries + backoff; cache last-known; tolerate missing PIDs.

### R4: Vehicle power instability

- Mitigation: graceful recovery on boot; avoid corruption-prone writes; future safe shutdown module.

---

## 15) Deliverables

- Working system meeting Acceptance Criteria
- Repo with documented build/run flows
- Docs:
  - `docs/PRD.md` (this)
  - `docs/ARCHITECTURE.md`
  - `docs/RUNBOOK.md`
- Config templates in `config/`

---

## 16) Appendix: UX Principles (non-negotiable)

1. No silent failure.
2. Modular survival.
3. Boot status shows progress if slow.
4. Web-first debugging.
5. Persistent status corner.
6. Safe failover placeholders for dead streams/sensors.
