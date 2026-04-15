"""
hand_tracker.py
---------------
MediaPipe-based hand tracking helper.
Exposes landmark positions and finger-tip distances for easy use.
"""

import cv2
import mediapipe as mp
import math


class HandTracker:
    def __init__(self, max_hands: int = 1, detection_confidence: float = 0.75,
                 tracking_confidence: float = 0.75):
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        # Landmark indices
        self.WRIST       = 0
        self.THUMB_TIP   = 4
        self.INDEX_TIP   = 8
        self.MIDDLE_TIP  = 12
        self.RING_TIP    = 16
        self.PINKY_TIP   = 20

    # -----------------------------------------------------------------
    def find_hands(self, frame: "np.ndarray", draw: bool = True):
        """
        Process frame and optionally draw hand skeleton.
        Returns the annotated frame and raw MediaPipe results.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.hands.process(rgb)
        rgb.flags.writeable = True

        if draw and self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )
        return frame, self.results

    # -----------------------------------------------------------------
    def get_landmarks(self, frame: "np.ndarray", hand_idx: int = 0):
        """
        Return pixel-space (x, y) for each landmark of the given hand.
        Returns None if no hand detected.
        """
        if not self.results.multi_hand_landmarks:
            return None

        h, w = frame.shape[:2]
        lms = self.results.multi_hand_landmarks[hand_idx].landmark
        return [(int(lm.x * w), int(lm.y * h)) for lm in lms]

    # -----------------------------------------------------------------
    def distance_between(self, landmarks, idx_a: int, idx_b: int):
        """Euclidean distance between two landmark points."""
        if landmarks is None:
            return None
        ax, ay = landmarks[idx_a]
        bx, by = landmarks[idx_b]
        return math.hypot(bx - ax, by - ay)

    # -----------------------------------------------------------------
    def midpoint(self, landmarks, idx_a: int, idx_b: int):
        """Pixel midpoint between two landmarks."""
        if landmarks is None:
            return None
        ax, ay = landmarks[idx_a]
        bx, by = landmarks[idx_b]
        return ((ax + bx) // 2, (ay + by) // 2)
