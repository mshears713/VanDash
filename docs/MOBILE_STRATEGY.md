# VanDash Mobile Strategy & Roadmap

## 📱 Core Objective

VanDash is designed to turn a mobile device (phone or tablet) into a dedicated, automotive-grade system display. By connecting the phone to the Raspberry Pi's local Access Point (AP), we achieve a high-bandwidth, zero-latency connection without needing the internet.

## 🛠️ Technology Choices

### 1. Progressive Web App (PWA)

* **Why**: Transform a website into an "App" without App Store approval.
* **Method**: Uses a `manifest.json` and `service-worker.js`.
* **Experience**: Provides a standalone window (no address bar), orientation locking (landscape), and a home screen icon.

### 2. High-Performance Gauges (Canvas API)

* **Why**: SVG can get "heavy" when updating 60 frames per second. Canvas is hardware-accelerated and light.
* **Designs to Explore**:
  * **Radial Dials**: Classic automotive instrumentation.
  * **Power Bars**: Modern industrial data visualization.
  * **Segmented Digital**: High-contrast, easy-to-read at a glance (glanceability).

## 🚀 Future Features

### 🎧 Voice & Audio

* **TTS Alerts**: *"Coolant over 100 degrees"* - essential for keeping eyes on the road.
* **Audio Chimes**: Subtle sonic feedback for system state changes.

### 🎮 Contextual UI

* **Gesture Control**: Swipe to switch between Rear Camera and Dashboard.
* **Proximity Dimming**: Auto-dimming based on night/day or phone sensor input.

### 📹 Video Stream Optimization

* **Low Latency**: Tuning the MJPEG stream or moving to WebRTC for "Real Mirror" response times.
