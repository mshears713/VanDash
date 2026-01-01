# VanDash Deployment Runbook

## 1. Quick Start (Web-First)

The primary diagnostic interface is the dashboard at `http://192.168.4.1/`.

1. Power on the Raspberry Pi.
2. Wait ~30 seconds for the Wi-Fi AP "VanDash-Hub" to appear.
3. Connect with your Android phone.
4. Navigate to `http://192.168.4.1/`.

## 2. Common Scenarios

### Subsystem is "FAULTY"

- **Symptom**: Red indicator in "Status Corner". Diag view shows "MANUAL RESET REQUIRED".
- **Action**: Check hardware connections (USB Video Capture, OBD Bluetooth Adapter). Restart the hub via the dashboard (if implemented) or power cycle.

### Camera is Offline

- **Symptom**: Black screen or placeholder in Reverse view.
- **Action**: Check if the USB video capture device is plugged into a blue USB 3.0 port. Check RCA cable connection from the camera.

### OBD Telemetry is Missing

- **Symptom**: Values show "--" or status is "WAITING".
- **Action**: Ensure the ignition is ON. Ensure the OBD adapter is paired/powered.

## 3. Advanced (SSH)

If the dashboard is unreachable:

1. Connect via Ethernet or check if AP is visible.
2. SSH into `pi@192.168.4.1`.
3. Check services:

   ```bash
   sudo systemctl status vandash-backend
   ```

4. View real-time logs:

   ```bash
   journalctl -u vandash-backend -f
   ```
