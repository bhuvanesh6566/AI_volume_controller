"""
ui_overlay.py
-------------
All OpenCV drawing helpers for the volume controller HUD.
Keeps main.py clean and readable.
"""

import cv2
import numpy as np


# ── Colour palette ─────────────────────────────────────────────────────────────
C_ACCENT   = (110, 86, 255)   # purple-blue  (BGR)
C_GREEN    = ( 56, 212, 111)  # mint green
C_RED      = ( 56,  56, 230)  # warm red
C_WHITE    = (255, 255, 255)
C_BLACK    = (  0,   0,   0)
C_YELLOW   = ( 20, 200, 240)
C_BG       = ( 20,  20,  30)  # dark navy (panel bg)
C_GLASS    = ( 40,  40,  55)  # glass panel
C_MUTED    = ( 80, 130, 255)  # muted indicator orange

FONT       = cv2.FONT_HERSHEY_SIMPLEX


# ── Helpers ────────────────────────────────────────────────────────────────────
def _alpha_blend(src, overlay, alpha: float):
    """Blend overlay onto src in-place with given alpha (0-1)."""
    cv2.addWeighted(overlay, alpha, src, 1 - alpha, 0, src)


def rounded_rect(img, x, y, w, h, r, color, thickness=-1):
    """Draw a rounded rectangle on img."""
    # Draw rectangles
    cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, thickness)
    cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, thickness)
    # Corners
    cv2.ellipse(img, (x + r,     y + r),     (r, r), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x + w - r, y + r),     (r, r), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x + r,     y + h - r), (r, r),  90, 0, 90, color, thickness)
    cv2.ellipse(img, (x + w - r, y + h - r), (r, r),   0, 0, 90, color, thickness)


# ── Volume bar ─────────────────────────────────────────────────────────────────
def draw_volume_bar(frame, volume_pct: int, muted: bool,
                    x=40, y_top=150, bar_h=300, bar_w=36):
    """Vertical gradient volume bar on the left side."""
    y_bot = y_top + bar_h

    # Background track
    rounded_rect(frame, x, y_top, bar_w, bar_h, 8, C_GLASS)

    if not muted and volume_pct > 0:
        fill_h = int(bar_h * volume_pct / 100)
        y_fill = y_bot - fill_h

        # Gradient fill (green → yellow → red)
        for i in range(fill_h):
            t = i / max(fill_h - 1, 1)
            if t < 0.5:
                b = int(56  + (20  - 56 ) * (t / 0.5))
                g = int(212 + (200 - 212) * (t / 0.5))
                r = int(111 + (240 - 111) * (t / 0.5))
            else:
                t2 = (t - 0.5) / 0.5
                b = int(20  + (56  - 20 ) * t2)
                g = int(200 + (56  - 200) * t2)
                r = int(240 + (230 - 240) * t2)
            py = y_fill + (fill_h - 1 - i)
            cv2.line(frame, (x + 2, py), (x + bar_w - 2, py), (b, g, r), 1)

        # Gloss line
        cv2.line(frame, (x + bar_w // 3, y_fill), (x + bar_w // 3, y_bot), (255, 255, 255), 1)

    # Notch marks
    for pct in [20, 40, 60, 80]:
        ny = y_bot - int(bar_h * pct / 100)
        cv2.line(frame, (x + bar_w, ny), (x + bar_w + 8, ny), C_WHITE, 1)
        cv2.putText(frame, f"{pct}", (x + bar_w + 10, ny + 5), FONT, 0.38, C_WHITE, 1)

    # Label
    label = "MUTED" if muted else f"{volume_pct}%"
    colour = C_MUTED if muted else C_WHITE
    lw = cv2.getTextSize(label, FONT, 0.7, 2)[0][0]
    cv2.putText(frame, label, (x + bar_w // 2 - lw // 2 - 5, y_bot + 28),
                FONT, 0.65, colour, 2)
    cv2.putText(frame, "VOL", (x + bar_w // 2 - 12, y_top - 12),
                FONT, 0.5, C_ACCENT, 2)


# ── Finger line + dots ─────────────────────────────────────────────────────────
def draw_finger_line(frame, pt_thumb, pt_index, mid, distance: float,
                     min_dist=30, max_dist=200, muted: bool = False):
    """Draw the thumb-index gesture on screen."""
    if muted:
        colour = C_MUTED
    else:
        t = max(0, min(1, (distance - min_dist) / (max_dist - min_dist)))
        r = int(56  + (230 - 56) * t)
        g = int(212 + (56  - 212) * t)
        b = int(111 + (56  - 111) * t)
        colour = (b, g, r)

    # Line
    cv2.line(frame, pt_thumb, pt_index, colour, 3)

    # Endpoint circles
    for pt in (pt_thumb, pt_index):
        cv2.circle(frame, pt, 12, colour,  -1)
        cv2.circle(frame, pt,  12, C_WHITE, 2)
        cv2.circle(frame, pt,  5,  C_WHITE, -1)

    # Midpoint pulse
    cv2.circle(frame, mid, 8, C_WHITE,  -1)
    cv2.circle(frame, mid, 8, colour,   -1)
    cv2.circle(frame, mid, 12, colour,   2)

    # Distance label
    cv2.putText(frame, f"{int(distance)}px", (mid[0] + 14, mid[1] - 8),
                FONT, 0.5, C_WHITE, 1)


# ── Info panel ─────────────────────────────────────────────────────────────────
def draw_info_panel(frame, fps: float, volume_pct: int, muted: bool, gesture_hint: str):
    """Bottom-right HUD panel."""
    h, w = frame.shape[:2]
    pw, ph = 280, 115
    px, py = w - pw - 15, h - ph - 15

    # Glass panel
    overlay = frame.copy()
    rounded_rect(overlay, px, py, pw, ph, 12, C_BG)
    _alpha_blend(frame, overlay, 0.7)
    rounded_rect(frame, px, py, pw, ph, 12, C_ACCENT, 2)

    # FPS
    fps_color = C_GREEN if fps >= 20 else C_YELLOW if fps >= 10 else C_RED
    cv2.putText(frame, f"FPS: {fps:.1f}", (px + 12, py + 28), FONT, 0.6, fps_color, 2)

    # Volume
    vol_text = "MUTED" if muted else f"Volume: {volume_pct}%"
    cv2.putText(frame, vol_text, (px + 12, py + 56), FONT, 0.6,
                C_MUTED if muted else C_WHITE, 2)

    # Gesture hint
    cv2.putText(frame, gesture_hint, (px + 12, py + 84), FONT, 0.48, C_ACCENT, 1)
    cv2.putText(frame, gesture_hint, (px + 12, py + 84), FONT, 0.48, C_WHITE, 1)


# ── Title ──────────────────────────────────────────────────────────────────────
def draw_title(frame):
    h, w = frame.shape[:2]
    # Semi-transparent top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 52), C_BG, -1)
    _alpha_blend(frame, overlay, 0.65)

    title = "  AI Volume Controller  |  Hand Gesture"
    cv2.putText(frame, title, (10, 36), FONT, 0.8, C_ACCENT, 2)
    cv2.putText(frame, title, (10, 36), FONT, 0.8, C_WHITE,  1)


# ── No-hand notice ─────────────────────────────────────────────────────────────
def draw_no_hand_notice(frame):
    h, w = frame.shape[:2]
    msg  = "Show your hand to the camera"
    tw   = cv2.getTextSize(msg, FONT, 0.9, 2)[0][0]
    cx   = (w - tw) // 2

    overlay = frame.copy()
    cv2.rectangle(overlay, (cx - 18, h // 2 - 32), (cx + tw + 18, h // 2 + 16),
                  C_BG, -1)
    _alpha_blend(frame, overlay, 0.6)

    cv2.putText(frame, msg, (cx, h // 2 + 4), FONT, 0.9, C_ACCENT, 3)
    cv2.putText(frame, msg, (cx, h // 2 + 4), FONT, 0.9, C_WHITE,  2)


# ── Mute toast ─────────────────────────────────────────────────────────────────
def draw_mute_toast(frame, muted: bool, alpha: float = 1.0):
    """Flashing centre toast when mute state changes."""
    h, w = frame.shape[:2]
    msg = "🔇 MUTED" if muted else "🔊 UNMUTED"
    tw = cv2.getTextSize(msg, FONT, 1.2, 3)[0][0]
    cx = (w - tw) // 2

    overlay = frame.copy()
    col = C_MUTED if muted else C_GREEN
    cv2.rectangle(overlay, (cx - 20, h // 2 - 48), (cx + tw + 20, h // 2 + 20),
                  col, -1)
    _alpha_blend(frame, overlay, 0.5 * alpha)
    cv2.putText(frame, msg, (cx, h // 2 + 8), FONT, 1.2, C_WHITE, 3)
