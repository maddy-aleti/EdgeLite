"""
confusion.py
─────────────────────────────────────────────────────────────────────────────
Confusion score calculator.

Confusion is a composite of four geometric sub-signals:

  1. Blink rate  — elevated blinking correlates with cognitive overload
  2. Head angle variance  — unstable head = confused searching / scanning
  3. Gaze loss  — looking away from the screen = not following content
  4. Micro-movement  — nose jitter = fidgeting under confusion

Each sub-signal is normalised to [0, 1] and combined as a weighted sum
defined in config.CONFUSION_WEIGHTS.

DESIGN NOTE:
  This module is intentionally stateless — it is a pure transformer that
  takes already-processed signals from the detector modules and returns a
  scalar score.  This keeps the confusion logic easy to test in isolation.

CPU / memory impact:
  4 float lookups + weighted sum.  Effectively zero cost.
"""

import config as cfg


class ConfusionScorer:
    """
    Computes a confusion score in [0, 100] from sub-signal inputs.

    Usage:
        scorer = ConfusionScorer()
        score = scorer.compute(blinks_per_min, head_variance,
                               gaze_loss, micro_movement)
    """

    def __init__(self):
        self.score: float = 0.0

    # ── Sub-signal normalisation ──────────────────────────────────────────────

    @staticmethod
    def _blink_rate_signal(blinks_per_minute: float) -> float:
        """
        Maps blinks/minute → [0, 1] confusion signal.

        Normal range: 8–25 blinks/min
          - Below LOW  → droopy / sleeping (not confused) → signal ≈ 0
          - Within range → normal → moderate signal
          - Above HIGH  → cognitive overload → signal → 1
        """
        low  = cfg.BLINK_RATE_LOW
        high = cfg.BLINK_RATE_HIGH
        if blinks_per_minute <= low:
            return 0.0
        if blinks_per_minute >= high:
            return 1.0
        return (blinks_per_minute - low) / (high - low)

    @staticmethod
    def _head_variance_signal(angle_variance: float) -> float:
        """
        angle_variance is already normalised [0, 1] by HeadPoseDetector.
        Pass through directly.
        """
        return min(float(angle_variance), 1.0)

    @staticmethod
    def _gaze_loss_signal(gaze_loss: float) -> float:
        """
        gaze_loss is already [0, 1] from EyeContactDetector.gaze_loss_score().
        Pass through directly.
        """
        return min(float(gaze_loss), 1.0)

    @staticmethod
    def _micro_movement_signal(micro_variance: float) -> float:
        """
        micro_variance: normalised nose position variance over confusion window.
        Clamp at 1.0.
        """
        return min(float(micro_variance), 1.0)

    # ── Main compute ──────────────────────────────────────────────────────────

    def compute(
        self,
        blinks_per_minute: float,
        head_angle_variance: float,
        gaze_loss: float,
        micro_movement: float,
    ) -> float:
        """
        Compute confusion score [0, 100].

        Args:
            blinks_per_minute   : from EARDetector.blinks_per_minute
            head_angle_variance : from HeadPoseDetector.angle_variance  (0–1)
            gaze_loss           : from EyeContactDetector.gaze_loss_score (0–1)
            micro_movement      : normalised nose position variance (0–1)

        Returns:
            Confusion score in [0, 100].
              0  = calm, fully following
              100 = high confusion indicators
        """
        w = cfg.CONFUSION_WEIGHTS

        blink_sig   = self._blink_rate_signal(blinks_per_minute)
        head_sig    = self._head_variance_signal(head_angle_variance)
        gaze_sig    = self._gaze_loss_signal(gaze_loss)
        micro_sig   = self._micro_movement_signal(micro_movement)

        raw = (
            w["blink_rate"]     * blink_sig  +
            w["head_variance"]  * head_sig   +
            w["gaze_reduction"] * gaze_sig   +
            w["micro_movement"] * micro_sig
        )

        self.score = round(min(raw * 100.0, 100.0), 1)
        return self.score
