# AI Volume Controller 🎛️

Control system volume with hand gestures using computer vision.

## Overview
Combines webcam-based hand tracking with system audio controls for a touch-free volume interface.

## Structure
- `main.py` — application entry point
- `hand_tracker.py` — hand tracking
- `volume_controller.py` — system volume control
- `ui_overlay.py` — on-screen overlay
- `requirements.txt` — dependencies

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

A webcam is required for gesture tracking.