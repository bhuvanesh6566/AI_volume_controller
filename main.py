"""
main.py  —  AI Hand Tracking Volume Controller
================================================
Controls Windows system speaker volume in real time using your webcam.

Gestures
--------
✋  Pinch (thumb ↔ index finger) ── controls volume   (open = loud, close = silent)
✊  Fist (all fingers closed)    ── toggles MUTE
👆  Index finger only up         ── shows subtle HUD hint

Usage
-----
  python main.py [--cam 0] [--width 1280] [--height 720]

Press  Q  or  ESC  to quit.
"""

import cv2
import time
import argparse
import numpy as np

from hand_tracker import HandTracker
from volume_controller import VolumeController
from ui_overlay import (
    draw_title, draw_volume_bar, draw_finger_line,
    draw_info_panel, draw_no_hand_notice, draw_mute_toast,
)


# ── Constants ──────────────────────────────────────────────────────────────────
DIST_MIN   = 28    # px distance thumb↔index that maps to   0 % volume
DIST_MAX   = 220   # px distance thumb↔index that maps to 100 % volume
SMOOTH_FACTOR = 0.18    # EMA smoothing (lower = smoother but more lag)

FIST_HOLD_FRAMES  = 12   # frames all fingers must be closed to trigger mute
TOAST_DURATION    = 1.5  # seconds to show mute toast


# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="AI Hand-Tracking Volume Controller")
    p.add_argument("--cam",    type=int, default=0,    help="Camera index (default 0)")
    p.add_argument("--width",  type=int, default=1280, help="Capture width")
    p.add_argument("--height", type=int, default=720,  help="Capture height")
    return p.parse_args()


def fingers_closed(landmarks, tracker: HandTracker):
    """
    Returns True when all four fingers (index→pinky) are curled down.
    Compares tip y-coordinate vs the MCP knuckle — if tip is BELOW knuckle
    (higher y value), the finger is folded.
    """
    # MCP (knuckle) indices: index=5, middle=9, ring=13, pinky=17
    tip_mcp = [(8, 5), (12, 9), (16, 13), (20, 17)]
    for tip_idx, mcp_idx in tip_mcp:
        tx, ty = landmarks[tip_idx]
        mx, my = landmarks[mcp_idx]
        if ty < my:          # tip above knuckle → finger up
            return False
    # Also check thumb: tip x vs IP joint x (for right hand, tip.x < IP.x)
    thumb_tip_x = landmarks[tracker.THUMB_TIP][0]
    thumb_ip_x  = landmarks[3][0]
    return True              # all four fingers down ⇒ fist


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # --- Initialise camera ---
    cap = cv2.VideoCapture(args.cam)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 60)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {args.cam}")

    tracker  = HandTracker(max_hands=1)
    vol_ctrl = VolumeController()

    # State
    smooth_vol    = vol_ctrl.get_volume_scalar()   # EMA-smoothed 0-1
    muted         = vol_ctrl.is_muted()
    fist_counter  = 0
    toast_timer   = 0.0
    prev_time     = time.time()
    fps           = 0.0
    gesture_hint  = "Pinch to control volume"

    print("=" * 50)
    print("  AI Volume Controller  --  running")
    print("  Pinch thumb+index  -> volume")
    print("  Make a fist        -> mute / unmute")
    print("  Press Q or ESC     -> quit")
    print("=" * 50)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)   # mirror so it feels natural

        # --- Hand tracking ---
        frame, results = tracker.find_hands(frame, draw=True)
        landmarks = tracker.get_landmarks(frame)

        now = time.time()
        dt  = now - prev_time
        fps = 0.9 * fps + 0.1 * (1.0 / max(dt, 1e-6))
        prev_time = now

        if landmarks:
            # ── Fist detection → mute toggle ──────────────────────────────
            if fingers_closed(landmarks, tracker):
                fist_counter += 1
                gesture_hint = f"Fist … ({fist_counter}/{FIST_HOLD_FRAMES})"
                if fist_counter == FIST_HOLD_FRAMES:
                    vol_ctrl.toggle_mute()
                    muted      = vol_ctrl.is_muted()
                    toast_timer = now + TOAST_DURATION
                    gesture_hint = "MUTED" if muted else "UNMUTED"
            else:
                fist_counter = 0

                # ── Pinch distance → volume ───────────────────────────────
                pt_thumb = landmarks[tracker.THUMB_TIP]
                pt_index = landmarks[tracker.INDEX_TIP]
                mid      = tracker.midpoint(landmarks, tracker.THUMB_TIP, tracker.INDEX_TIP)
                dist     = tracker.distance_between(landmarks, tracker.THUMB_TIP, tracker.INDEX_TIP)

                # Map distance to 0-1 scalar
                target_vol = clamp((dist - DIST_MIN) / (DIST_MAX - DIST_MIN), 0.0, 1.0)

                # Smooth with EMA
                smooth_vol += SMOOTH_FACTOR * (target_vol - smooth_vol)

                if not muted:
                    vol_ctrl.set_volume_scalar(smooth_vol)
                    muted = False

                gesture_hint = "Pinch: open=loud, close=quiet"

                # Draw gesture line
                draw_finger_line(frame, pt_thumb, pt_index, mid, dist,
                                 DIST_MIN, DIST_MAX, muted)

        else:
            fist_counter = 0
            gesture_hint = "Show your hand to the camera"
            draw_no_hand_notice(frame)

        # Sync actual system volume to display (it might change externally)
        actual_vol_pct = round(smooth_vol * 100) if not muted else vol_ctrl.get_volume_percent()
        if muted:
            actual_vol_pct = 0

        # ── Draw HUD ──────────────────────────────────────────────────────
        draw_title(frame)
        draw_volume_bar(frame, actual_vol_pct, muted)
        draw_info_panel(frame, fps, actual_vol_pct, muted, gesture_hint)

        # Mute toast
        if now < toast_timer:
            alpha = min(1.0, (toast_timer - now) / 0.4)  # fade out in last 0.4 s
            draw_mute_toast(frame, muted, alpha)

        # ── Show ──────────────────────────────────────────────────────────
        cv2.imshow("AI Volume Controller", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):   # Q or ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Exited cleanly.")


if __name__ == "__main__":
    main()
