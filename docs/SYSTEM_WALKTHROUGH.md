# VanDash System Walkthrough

This document helps you understand how VanDash works "under the hood" without needing to read every line of code. It is designed for an operator who knows a bit of coding and wants to know how the gears turn.

---

## 1. The Project Structure

Think of VanDash as two separate houses connected by a bridge:

* **`backend/` (The Engine Room)**: This is where the Python code lives. It talks to the camera, the vehicle's computer (OBD), and monitors the system's temperature. It "produces" all the data.
* **`frontend/` (The Dashboard)**: This is the React/TypeScript code. It's the "face" of the system. It runs in your Android phone's browser and "consumes" the data from the backend to show you pretty gauges and video.
* **`config/`**: Contains settings like your Wi-Fi name and whether to use "Simulation Mode" (fake data for testing).
* **`docs/`**: Where this walkthrough, the runbook, and the architecture maps live.
* **`scripts/`**: Helpful tools to install or start the system automatically on a Raspberry Pi.

---

## 2. Configuration: Telling the System What to Do

VanDash uses a **Centralized Config** (located in `config/example.yaml`).

When the backend starts, it reads this file. It tells the system things like:

* "Should I look for a real camera or just show a test animation?" (`simulation: true/false`)
* "What is the name of the Wi-Fi network I should create?"
* "How many times should I try to restart a broken sensor before giving up?" (`max_retries`)

This means you can change how the system behaves just by editing a text file, rather than digging through the Python code.

---

## 3. The Startup Sequence (From Power-On to UI)

When you flip the switch in your van, here is what happens:

1. **Linux Boots**: The Raspberry Pi starts its operating system (Raspberry Pi OS).
2. **Systemd Takes Over**: A manager called `systemd` looks at the file in `scripts/vandash-backend.service` and realizes, "I need to start the VanDash engine!"
3. **FastAPI Wakes Up**: The backend server starts. Its first job is to start the "Sub-Services" (Camera and OBD loops).
4. **The Loops Begin**:
    * The **Camera Service** starts looking for a USB device and grabs frames 30 times a second.
    * The **OBD Service** tries to find your Bluetooth adapter and starts asking the car for its RPM.
5. **Wi-Fi Appears**: The Pi creates a Wi-Fi network. Once your phone connects and you go to `192.168.4.1`, the backend hands your phone the **Frontend Build** (the UI).

---

## 4. Health Monitoring: "Self-Healing"

One of the most important parts of VanDash is that it **monitors itself**. Every major part of the system (Camera, OBD, Networking) is treated as a "Subsystem."

### How it detects failures

Each service (like the OBD service) runs in its own "loop." If a loop hits an error (e.g., the Bluetooth adapter is unplugged), it doesn't crash the whole system. Instead:

1. The service tells the **Health Supervisor**: "Hey, I just had an error!"
2. The Health Supervisor records the error message and increments a **Restart Counter**.
3. The service waits a few seconds (Backoff) and tries again.

### The "Supervision" Policy

To prevent the system from getting stuck in an infinite loop of trying to fix something that is truly broken, we have a **Max Retry Policy**:

* If a service fails **3 times in a row**, the Supervisor says "Stop."
* The subsystem is marked as **FAULTY** (Red) in your dashboard.
* The dashboard shows **"MANUAL RESET REQUIRED"**.

This keeps the system stable and tells you exactly which wire you need to go jiggle.

---

## 5. Summary

VanDash is built to be **Resilient**. The backend does the heavy lifting of talking to hardware, the frontend makes it easy to see, and the Health Supervisor makes sure you always know exactly what is happening, even when something breaks.
