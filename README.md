# AI Volume Controller 🎛️

Control system volume with hand gestures using computer vision.

## Overview
This project combines webcam-based hand tracking with system audio controls to provide a touch-free volume interface.

## Project Structure
- `main.py` — application entry point
- `hand_tracker.py` — hand tracking logic
- `volume_controller.py` — system volume control
- `ui_overlay.py` — on-screen UI/overlay
- `requirements.txt` — Python dependencies

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Notes
A webcam is required for gesture tracking. Platform-specific audio-control behavior may vary.
