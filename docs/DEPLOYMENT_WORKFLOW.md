# VanDash Deployment Workflow

VanDash follows a **Laptop-Build, Pi-Run** model. The Raspberry Pi is treated as a sealed appliance, and the laptop is the workshop.

---

## 1. Development: Maintenance Mode

All coding and initial hardware testing happens on your **laptop**.

1. **Switch to Maintenance**: Ensure `config/maintenance.yaml` exists.
2. **Start Backend**:

    ```bash
    cd backend
    uv run uvicorn app.main:app --reload
    ```

3. **Hardware Probing**: If you want to find a camera index or OBD port:
    * Set `allow_real: true` in `maintenance.yaml`.
    * Plug in the device.
    * Watch the logs in the **Diag** view. The system will tell you if it sees the hardware or if it's staying in simulation.

---

## 2. Preparation: The AP Boundary

Before deploying, you must connect your laptop to the "VanDash-Hub" Wi-Fi network produced by the Pi.

* **SSID**: VanDash-Hub
* **IP**: 192.168.4.1

---

## 3. Deployment: One-Command Sync

Once connected to the Pi's Wi-Fi, run the deployment script from the root of the project:

```bash
./scripts/deploy_to_pi.sh
```

### What the script does

1. **Compiles** the React frontend into static assets on your laptop.
2. **Syncs** only the production files (Backend code + Built Frontend) to the Pi via `rsync`.
3. **Restarts** the backend service on the Pi so the new code takes effect.

---

## 4. Verification: Operational Mode

Once the script finishes:

1. Verify the Pi is in `operational` mode by checking `config/operational.yaml` (which stays on the Pi).
2. Open `http://192.168.4.1/` in your browser.
3. Navigate to the **Diag** view.
4. Check that all subsystems are **ACTIVE** with 0 restarts.

---

## 5. Troubleshooting

* **Permission Denied**: Ensure you have SSH keys set up for the `pi` user, or be prepared to type the password during the script.

* **Rsync Missing**: The script uses `rsync`. If you are on pure Windows (not WSL/Git Bash), you may need to install it.

* **Service Restart Fails**: Check `journalctl -u vandash-backend -f` on the Pi via SSH to see why the backend isn't starting.
