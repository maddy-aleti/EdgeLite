"""
gesture.py
─────────────────────────────────────────────────────────────────────────────
Head gesture detector — nod (yes) and shake (no) via oscillation analysis.

HOW IT WORKS:
  Gesture detection is based on counting direction reversals (zero-crossings
  of the velocity signal) in a short rolling window.

  Head nod → nose Y-coordinate oscillates UP → DOWN → UP
             Detected as ≥ N sign changes in dY over GESTURE_WINDOW frames.

  Head shake → nose X-coordinate oscillates LEFT → RIGHT → LEFT
              Detected as ≥ N sign changes in dX over GESTURE_WINDOW frames.

  A deadzone filters out micro-tremors so only deliberate movements register.

WHY OSCILLATION AND NOT FFT?
  FFT requires numpy.fft, introduces O(N log N) overhead per call, and requires
  knowledge of the dominant frequency band.  For gestures happening at ~1–2 Hz
  in a 45-frame window, simple zero-crossing counting is sufficient, O(N),
  and fully explainable.

CPU / memory impact:
  Two deques of GESTURE_WINDOW floats for raw positions.
  Two deques of sign integers for derivatives.
  Sign-change counting: O(N) over ~45 floats — ~2 μs.
  Total memory: < 2 KB.
"""

from collections import deque
import numpy as np

from landmarks import nose_position_normalised
import config as cfg


class GestureDetector:
    """
    Stateful gesture detector.  Call update(lm_xy) once per frame.

    Published attributes:
        head_nod   : True when a nod gesture was just confirmed
        head_shake : True when a shake gesture was just confirmed
        nod_cooldown_frames   : remaining cooldown frames (prevents double-fire)
        shake_cooldown_frames : same for shake
    """

    # Cooldown (in frames) after a gesture fires to prevent repeated triggers
    _COOLDOWN = 20

    def __init__(self):
        # Nose position history (normalised coordinates)
        self._x_history: deque = deque(maxlen=cfg.GESTURE_WINDOW)
        self._y_history: deque = deque(maxlen=cfg.GESTURE_WINDOW)

        # Published gestures — True for exactly one frame when detected
        self.head_nod:   bool = False
        self.head_shake: bool = False

        # Cooldown counters
        self._nod_cooldown:   int = 0
        self._shake_cooldown: int = 0

    # ── Oscillation counting ──────────────────────────────────────────────────

    @staticmethod
    def _count_oscillations(history: deque, deadzone: float) -> int:
        """
        Count the number of direction reversals in a position history.

        A reversal is counted each time the sign of the velocity changes
        (after deadzone filtering).

        Args:
            history  : deque of normalised position values
            deadzone : minimum delta to register as movement

        Returns:
            Number of oscillation cycles (sign changes / 2).
        """
        arr = np.array(history, dtype=np.float32)
        if len(arr) < 3:
            return 0

        # Velocity (frame-to-frame difference)
        delta = np.diff(arr)

        # Apply deadzone: set sub-threshold deltas to 0
        delta[np.abs(delta) < deadzone] = 0.0

        # Remove zeros so sign() is reliable
        delta = delta[delta != 0.0]
        if len(delta) < 2:
            return 0

        signs = np.sign(delta)
        # Count sign changes
        sign_changes = int(np.sum(signs[1:] != signs[:-1]))
        # Each full oscillation requires 2 sign changes (peak + trough)
        return sign_changes // 2

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, lm_xy: np.ndarray) -> None:
        """
        Process one frame.

        Args:
            lm_xy: float32 array (N, 2) from landmarks.landmarks_to_xy()
        """
        # 1. Nose position normalised to face bounding box
        nx, ny = nose_position_normalised(lm_xy)
        self._x_history.append(nx)
        self._y_history.append(ny)

        # Decrement cooldowns
        if self._nod_cooldown > 0:
            self._nod_cooldown -= 1
        if self._shake_cooldown > 0:
            self._shake_cooldown -= 1

        # 2. Count oscillations in each axis
        vert_osc = self._count_oscillations(self._y_history, cfg.GESTURE_DEADZONE)
        horiz_osc = self._count_oscillations(self._x_history, cfg.GESTURE_DEADZONE)

        # 3. Fire gesture if oscillation count meets threshold and not in cooldown
        if vert_osc >= cfg.NOD_OSCILLATIONS and self._nod_cooldown == 0:
            self.head_nod = True
            self._nod_cooldown = self._COOLDOWN
        else:
            self.head_nod = False

        if horiz_osc >= cfg.SHAKE_OSCILLATIONS and self._shake_cooldown == 0:
            self.head_shake = True
            self._shake_cooldown = self._COOLDOWN
        else:
            self.head_shake = False

    def reset(self) -> None:
        self.__init__()
