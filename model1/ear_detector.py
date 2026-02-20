"""
ear_detector.py
─────────────────────────────────────────────────────────────────────────────
Eye Aspect Ratio (EAR) based blink counter and sleep detector.

THEORY:
  Drozdzal et al. showed that EAR reliably drops when eyelids close.
  Formula:  EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
  p1..p6 are the six-point eye model landmarks.

  Open eye  → EAR ≈ 0.25–0.32
  Blinking  → EAR drops below threshold for 1–3 frames
  Sleeping  → EAR stays below deep-sleep threshold for seconds

CPU / memory impact:
  6 + 6 = 12 landmark lookups per frame, 6 euclidean distance calls.
  State maintained in two small integer counters + one fixed-size deque.
  Total memory: < 1 KB.
"""

from collections import deque
import numpy as np

from landmarks import (
    LEFT_EYE_EAR, RIGHT_EYE_EAR,
    eye_aspect_ratio,
)
import config as cfg


class EARDetector:
    """
    Stateful EAR processor.  Call update(lm_xy) once per frame.

    Tracks:
      - Per-frame EAR values (left, right, average)
      - Blink count within a rolling window
      - Consecutive-frame closed-eye counter → sleep detection
    """

    def __init__(self):
        # Rolling window of EAR averages for smoothing
        self._ear_history: deque = deque(maxlen=cfg.SMOOTHING_WINDOW)

        # Blink event timestamps (frame numbers) within BLINK_WINDOW
        self._blink_frames: deque = deque(maxlen=200)   # preallocated ring buffer

        # Consecutive frames where EAR < EAR_THRESHOLD → blink in progress
        self._blink_counter: int = 0

        # Consecutive frames where EAR < SLEEP_EAR_THRESHOLD → sleep
        self._sleep_counter: int = 0

        # Persistent totals
        self.total_blinks: int = 0
        self.current_frame: int = 0

        # Published results (updated each call to update())
        self.ear_left:  float = 0.0
        self.ear_right: float = 0.0
        self.ear_avg:   float = 0.0
        self.is_blinking: bool = False
        self.is_sleeping: bool = False
        self.blinks_in_window: int = 0   # blinks in last BLINK_WINDOW frames
        self.blinks_per_minute: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, lm_xy: np.ndarray) -> None:
        """
        Process one frame's landmark array.  Updates all published attributes.

        Args:
            lm_xy: float32 array (N, 2) from landmarks.landmarks_to_xy()
        """
        self.current_frame += 1

        # 1. Compute EAR for both eyes
        self.ear_left  = eye_aspect_ratio(lm_xy, LEFT_EYE_EAR)
        self.ear_right = eye_aspect_ratio(lm_xy, RIGHT_EYE_EAR)
        self.ear_avg   = (self.ear_left + self.ear_right) / 2.0

        self._ear_history.append(self.ear_avg)

        # 2. Smoothed EAR (average over window) for thresholding
        smooth_ear = float(np.mean(self._ear_history))

        # 3. Blink detection — wait for EAR to drop THEN rise
        if smooth_ear < cfg.EAR_THRESHOLD:
            self._blink_counter += 1
            self.is_blinking = True
        else:
            if self._blink_counter >= cfg.EAR_CONSEC_FRAMES:
                # Eye just re-opened after sustained closure → count blink
                self.total_blinks += 1
                self._blink_frames.append(self.current_frame)
            self._blink_counter = 0
            self.is_blinking = False

        # 4. Sleep detection — sustained EAR below tighter threshold
        if smooth_ear < cfg.SLEEP_EAR_THRESHOLD:
            self._sleep_counter += 1
        else:
            self._sleep_counter = 0

        self.is_sleeping = self._sleep_counter >= cfg.SLEEP_CONSEC_FRAMES

        # 5. Blink rate within rolling window
        cutoff = self.current_frame - cfg.BLINK_WINDOW
        # Purge old blink records from the left end of the deque
        while self._blink_frames and self._blink_frames[0] < cutoff:
            self._blink_frames.popleft()

        self.blinks_in_window = len(self._blink_frames)

        # Convert window count to blinks/minute
        # window_seconds = BLINK_WINDOW / TARGET_FPS
        window_seconds = cfg.BLINK_WINDOW / max(cfg.TARGET_FPS, 1)
        self.blinks_per_minute = (self.blinks_in_window / window_seconds) * 60.0

    def normalised_ear(self) -> float:
        """
        Return EAR normalised to [0, 1] for use in engagement scoring.
        Maps EAR 0 → 0.0, EAR ≥ 0.30 → 1.0 (fully open).
        """
        return min(self.ear_avg / 0.30, 1.0)

    def reset(self) -> None:
        """Reset all state (e.g. on new session start)."""
        self.__init__()
