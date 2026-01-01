# VanDash v1 Architecture

## System Topology

```mermaid
graph TD
    subgraph "Raspberry Pi (Hub)"
        AP[Wi-Fi Access Point]
        FastAPI[FastAPI Backend]
        Health[Health Supervision]
        Camera[Camera Service - OpenCV]
        OBD[OBD Service - python-obd]
        Logging[Logging Service]
        
        FastAPI --> Health
        FastAPI --> Logging
        Camera --> FastAPI
        OBD --> FastAPI
    end
    
    subgraph "Hardware"
        RCA[Analog Camera] -->|RCA| USB[USB Capture Card]
        USB -->|UVC| Camera
        Vehicle[Vehicle ECU] -->|OBD-II| BT[Bluetooth Adapter]
        BT -->|Serial| OBD
    end
    
    subgraph "Client"
        Android[Android Browser]
        React[React SPA]
        
        Android -->|HTTP/SSE| AP
        React -->|Requests| FastAPI
    end
```

## Key Designs

1. **Offline-First**: No internet required. Local AP provides DNS and Static IP (192.168.4.1).
2. **Resilience**: Subsystems run in isolated threads. Failure in one (e.g., OBD) does not crash the Dashboard.
3. **Low Latency**: Rear camera uses MJPEG streaming for near-live response during reversing.
4. **Observability**: Every service state is tracked. Errors are surfaced to the UI, not hidden in logs.
