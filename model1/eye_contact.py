"""
eye_contact.py
─────────────────────────────────────────────────────────────────────────────
Eye contact / on-screen gaze detection using nose-to-face-center alignment.

THEORY:
  When a student looks at the screen directly in front of them, the nose tip
  sits close to the horizontal centre of the face bounding box.

  Deviation formula:
    deviation = (nose_x - face_center_x) / face_width

  A small |deviation| → student is looking forward (eye contact with screen).
  Large |deviation| or large vertical deviation → looking away.

  This is a proxy metric — it approximates yaw without a full 3-D PnP solve,
  which avoids the runtime overhead of solving a 6-DoF pose.

Why not use iris tracking?
  MediaPipe iris landmarks (468, 473) are available but their x/y alone do
  not reliably indicate gaze direction without knowing the eye-socket geometry.
  The nose approach is simpler, cheaper, and sufficient for in-classroom use.

CPU / memory impact:
  2 landmark lookups + 3 arithmetic ops per frame.
  Rolling deque of SMOOTHING_WINDOW floats → < 1 KB.
"""

from collections import deque
import numpy as np

from landmarks import nose_face_deviation
import config as cfg


class EyeContactDetector:
    """
    Stateful eye-contact tracker.  Call update(lm_xy) once per frame.

    Published attributes:
        deviation          : raw nose-to-center normalised deviation
        smoothed_deviation : rolling average (more stable)
        eye_contact        : True when student appears to look forward
        contact_ratio      : fraction of frames with eye contact (rolling window)
    """

    def __init__(self):
        # Rolling window for smoothing
        self._deviation_history: deque = deque(maxlen=cfg.SMOOTHING_WINDOW)

        # Rolling window for contact ratio (for confusion/engagement scoring)
        self._contact_history: deque = deque(maxlen=cfg.ENGAGEMENT_WINDOW)

        # Published results
        self.deviation: float          = 0.0
        self.smoothed_deviation: float = 0.0
        self.eye_contact: bool         = True
        self.contact_ratio: float      = 1.0   # 0–1; 1 = always looking forward

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, lm_xy: np.ndarray) -> None:
        """
        Process one frame.

        Args:
            lm_xy: float32 array (N, 2) from landmarks.landmarks_to_xy()
        """
        # 1. Raw deviation of nose from face centre
        self.deviation = nose_face_deviation(lm_xy)
        self._deviation_history.append(abs(self.deviation))

        # 2. Smoothed deviation
        self.smoothed_deviation = float(np.mean(self._deviation_history))

        # 3. Binary eye-contact decision
        self.eye_contact = self.smoothed_deviation <= cfg.EYE_CONTACT_NOSE_TOLERANCE

        # 4. Rolling contact ratio
        self._contact_history.append(1 if self.eye_contact else 0)
        self.contact_ratio = float(np.mean(self._contact_history))

    def gaze_loss_score(self) -> float:
        """
        Returns [0, 1] where 1 = completely off-screen, 0 = always on-screen.
        Used as a sub-signal in confusion scoring.
        """
        return 1.0 - self.contact_ratio

    def reset(self) -> None:
        self.__init__()
