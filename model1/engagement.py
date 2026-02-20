"""
engagement.py
─────────────────────────────────────────────────────────────────────────────
Engagement score calculator.

Engagement is a composite of four positive signals minus a confusion penalty:

  1. Eye openness  — EAR-based: open eyes indicate active attention
  2. Head stability  — inverse variance: still head = focused
  3. Eye contact  — on-screen gaze ratio: looking at content
  4. Confusion penalty  — subtracted when confusion is high

The result is scaled to [0, 100] with a rolling temporal smoother to prevent
score flickering from single-frame noise.

CPU / memory impact:
  Deque of ENGAGEMENT_WINDOW floats + 4 arithmetic ops.
  Negligible.  <1 KB.
"""

from collections import deque
import numpy as np

import config as cfg


class EngagementScorer:
    """
    Computes a smoothed engagement score in [0, 100].

    Usage:
        scorer = EngagementScorer()
        score = scorer.compute(ear_norm, head_stability,
                               contact_ratio, confusion_score)
    """

    def __init__(self):
        # Temporal smoother over engagement window
        self._score_history: deque = deque(maxlen=cfg.ENGAGEMENT_WINDOW)
        self.score: float  = 50.0
        self.raw_score: float = 50.0

    # ── Main compute ──────────────────────────────────────────────────────────

    def compute(
        self,
        ear_normalised: float,        # [0, 1] from EARDetector.normalised_ear()
        head_stability: float,        # [0, 1] from HeadPoseDetector.normalised_stability()
        contact_ratio: float,         # [0, 1] from EyeContactDetector.contact_ratio
        confusion_score: float,       # [0, 100] from ConfusionScorer.score
    ) -> float:
        """
        Compute smoothed engagement score [0, 100].

        Args:
            ear_normalised    : normalised EAR; 1 = fully open eyes
            head_stability    : 1 = perfectly still head
            contact_ratio     : 1 = always looking at screen
            confusion_score   : 0–100 confusion indicator

        Returns:
            Smoothed engagement score in [0, 100].
              0  = disengaged / sleeping / confused
              100 = fully alert and focused
        """
        w = cfg.ENGAGEMENT_WEIGHTS

        # Confusion normalised to [0, 1] for weight application
        confusion_norm = confusion_score / 100.0

        # Positive signals
        positive = (
            w["eye_openness"]     * ear_normalised  +
            w["head_stability"]   * head_stability  +
            w["eye_contact"]      * contact_ratio
        )

        # Confusion penalty subtracts from positive score
        penalty = w["confusion_penalty"] * confusion_norm

        # Clamp to [0, 1]
        raw = max(0.0, min(positive - penalty, 1.0))
        self.raw_score = round(raw * 100.0, 1)

        # Temporal smoothing
        self._score_history.append(self.raw_score)
        self.score = round(float(np.mean(self._score_history)), 1)

        return self.score

    def reset(self) -> None:
        self.__init__()
