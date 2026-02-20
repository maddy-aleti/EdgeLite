"""
head_pose.py
─────────────────────────────────────────────────────────────────────────────
Head roll-tilt detection and micro-movement variance tracker.

THEORY:
  Head tilt (roll) is the simplest and most reliable pose metric derivable
  from 2-D landmarks without a full 3-D PnP solve.

  angle = atan2(dy, dx)  where dy/dx is the eye-corner vector.

  This is NOT pitch or yaw — those require full perspective projection.
  For attention monitoring, roll is the most behaviorally meaningful axis:
  a student leaning / dozing produces large roll angles.

  Micro-movement: rolling variance of head angle over a short window.
  High variance = fidgeting / confusion; near-zero = stable engagement.

CPU / memory impact:
  Two deques of floats (SMOOTHING_WINDOW + CONFUSION_WINDOW frames each).
  One atan2 per frame — completely negligible.
  Total memory: ~few KB.
"""

from collections import deque
import numpy as np

from landmarks import eye_tilt_angle
import config as cfg


class HeadPoseDetector:
    """
    Stateful head-pose processor.  Call update(lm_xy) once per frame.

    Published attributes:
        tilt_angle_deg  : current raw tilt angle in degrees
        smoothed_angle  : rolling-average smoothed angle
        is_tilted       : True when sustained tilt exceeds threshold
        angle_variance  : normalised variance over confusion window
    """

    def __init__(self):
        # Rolling angle history for smoothing
        self._angle_history: deque = deque(maxlen=cfg.SMOOTHING_WINDOW)

        # Longer window for variance (confusion signal)
        self._var_history: deque = deque(maxlen=cfg.CONFUSION_WINDOW)

        # Consecutive tilt-alert frames
        self._tilt_counter: int = 0

        # Published results
        self.tilt_angle_deg: float = 0.0
        self.smoothed_angle: float = 0.0
        self.is_tilted:       bool = False
        self.angle_variance:  float = 0.0    # normalised [0, 1]

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, lm_xy: np.ndarray) -> None:
        """
        Process one frame's landmark array.

        Args:
            lm_xy: float32 array (N, 2) from landmarks.landmarks_to_xy()
        """
        # 1. Raw tilt angle
        self.tilt_angle_deg = eye_tilt_angle(lm_xy)

        # 2. Append to histories
        self._angle_history.append(self.tilt_angle_deg)
        self._var_history.append(self.tilt_angle_deg)

        # 3. Smoothed angle
        self.smoothed_angle = float(np.mean(self._angle_history))

        # 4. Tilt state — sustained deviation
        if abs(self.smoothed_angle) > cfg.TILT_THRESHOLD_DEG:
            self._tilt_counter += 1
        else:
            self._tilt_counter = 0

        self.is_tilted = self._tilt_counter >= cfg.TILT_CONSEC_FRAMES

        # 5. Angle variance (normalised)
        #    Raw variance in degrees² — divide by HEAD_VAR_HIGH to normalise to [0,1]
        raw_var = float(np.var(self._var_history)) if len(self._var_history) > 1 else 0.0
        # HEAD_VAR_HIGH is in normalised units but angle variance is in degrees² —
        # use empirical scaling: 50 deg² ≈ "very high" variance
        self.angle_variance = min(raw_var / 50.0, 1.0)

    def normalised_stability(self) -> float:
        """
        Returns head stability [0, 1] = 1 − angle_variance.
        Used by engagement scoring: stable head → high engagement.
        """
        return 1.0 - self.angle_variance

    def reset(self) -> None:
        self.__init__()
