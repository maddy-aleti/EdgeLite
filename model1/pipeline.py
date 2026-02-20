"""
pipeline.py
─────────────────────────────────────────────────────────────────────────────
EngagementPipeline — the main orchestrator for all inference modules.

This class owns:
  - The MediaPipe FaceLandmarker task (loaded once)
  - All detector/scorer instances
  - The CSV logger

Call process_frame(bgr_frame) once per frame → get back an EngagementResult.

DESIGN PRINCIPLES:
  1. MediaPipe model is loaded ONCE in __init__ — never in the loop.
  2. All detector state lives inside detector objects — pipeline is just a router.
  3. No numpy allocations inside the hot path beyond landmarks_to_xy().
  4. Micro-movement variance is computed here using nose position history
     because it spans the intersection of head-pose and eye-contact logic.

CPU / memory impact:
  Dominant cost: MediaPipe FaceLandmarker inference ~15–25 ms on modern CPU.
  All post-processing adds < 2 ms.
  Peak RAM: ~80–120 MB (model weights loaded into RAM).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np

# MediaPipe Python bindings
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# Local modules
import config as cfg
from landmarks import landmarks_to_xy, nose_position_normalised
from ear_detector    import EARDetector
from head_pose       import HeadPoseDetector
from eye_contact     import EyeContactDetector
from confusion       import ConfusionScorer
from engagement      import EngagementScorer
from gesture         import GestureDetector
from logger          import SessionLogger


# ─── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class EngagementResult:
    """
    Snapshot of all metrics for a single processed frame.
    Passed back to main.py for display and logging.
    """
    frame_number:      int   = 0
    face_detected:     bool  = False
    fps:               float = 0.0
    inference_ms:      float = 0.0

    # EAR
    ear_left:          float = 0.0
    ear_right:         float = 0.0
    ear_avg:           float = 0.0
    is_blinking:       bool  = False
    is_sleeping:       bool  = False
    blink_count:       int   = 0
    blinks_per_minute: float = 0.0

    # Head pose
    tilt_angle_deg:    float = 0.0
    is_tilted:         bool  = False

    # Eye contact
    eye_contact:       bool  = True
    contact_ratio:     float = 1.0

    # Scores
    confusion_score:   float = 0.0
    engagement_score:  float = 50.0

    # Gestures
    head_nod:          bool  = False
    head_shake:        bool  = False


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class EngagementPipeline:
    """
    Full inference pipeline from BGR frame → EngagementResult.

    Args:
        log_csv  : Whether to write a CSV session log (default True).
        log_path : Optional explicit CSV path override.
    """

    def __init__(self, log_csv: bool = True, log_path: str | None = None):
        # ── Load MediaPipe FaceLandmarker (ONCE) ──────────────────────────────
        print("[Pipeline] Loading MediaPipe FaceLandmarker…", end=" ", flush=True)
        base_options = mp_python.BaseOptions(model_asset_path=cfg.MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=cfg.NUM_FACES,
            min_face_detection_confidence=cfg.MIN_FACE_CONFIDENCE,
            min_tracking_confidence=cfg.MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        print("OK")

        # ── Detector / scorer instances ───────────────────────────────────────
        self._ear     = EARDetector()
        self._head    = HeadPoseDetector()
        self._gaze    = EyeContactDetector()
        self._gesture = GestureDetector()
        self._confusion  = ConfusionScorer()
        self._engagement = EngagementScorer()

        # Micro-movement variance buffer (nose position history)
        self._nose_x_history: deque = deque(maxlen=cfg.CONFUSION_WINDOW)
        self._nose_y_history: deque = deque(maxlen=cfg.CONFUSION_WINDOW)

        # ── CSV Logger ────────────────────────────────────────────────────────
        self._logger = SessionLogger(log_path) if log_csv else None

        # ── FPS tracking ──────────────────────────────────────────────────────
        self._frame_times: deque = deque(maxlen=30)
        self._frame_number: int = 0

    # ── Core processing ───────────────────────────────────────────────────────

    def process_frame(self, bgr_frame: np.ndarray) -> EngagementResult:
        """
        Run the full pipeline on one BGR OpenCV frame.

        Args:
            bgr_frame: uint8 numpy array (H, W, 3) from cv2.VideoCapture.

        Returns:
            EngagementResult with all metrics populated.
        """
        t_start = time.perf_counter()
        self._frame_number += 1

        result = EngagementResult(frame_number=self._frame_number)

        # ── FPS computation ───────────────────────────────────────────────────
        self._frame_times.append(t_start)
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            result.fps = round((len(self._frame_times) - 1) / max(elapsed, 1e-6), 1)

        # ── MediaPipe inference ───────────────────────────────────────────────
        # Convert BGR (OpenCV) → RGB (MediaPipe)
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        detection = self._landmarker.detect(mp_image)

        t_infer = time.perf_counter()
        result.inference_ms = round((t_infer - t_start) * 1000, 1)

        # ── No face detected ─────────────────────────────────────────────────
        if not detection.face_landmarks:
            result.face_detected = False
            return result

        result.face_detected = True
        h, w = bgr_frame.shape[:2]

        # ── Convert landmarks to pixel array (done ONCE per frame) ───────────
        lm_xy = landmarks_to_xy(detection.face_landmarks[0], w, h)

        # ── EAR / sleep / blink ───────────────────────────────────────────────
        self._ear.update(lm_xy)
        result.ear_left          = self._ear.ear_left
        result.ear_right         = self._ear.ear_right
        result.ear_avg           = self._ear.ear_avg
        result.is_blinking       = self._ear.is_blinking
        result.is_sleeping       = self._ear.is_sleeping
        result.blink_count       = self._ear.total_blinks
        result.blinks_per_minute = self._ear.blinks_per_minute

        # ── Head tilt ─────────────────────────────────────────────────────────
        self._head.update(lm_xy)
        result.tilt_angle_deg = self._head.tilt_angle_deg
        result.is_tilted      = self._head.is_tilted

        # ── Eye contact ───────────────────────────────────────────────────────
        self._gaze.update(lm_xy)
        result.eye_contact   = self._gaze.eye_contact
        result.contact_ratio = self._gaze.contact_ratio

        # ── Gesture detection ─────────────────────────────────────────────────
        self._gesture.update(lm_xy)
        result.head_nod   = self._gesture.head_nod
        result.head_shake = self._gesture.head_shake

        # ── Micro-movement variance ───────────────────────────────────────────
        nx, ny = nose_position_normalised(lm_xy)
        self._nose_x_history.append(nx)
        self._nose_y_history.append(ny)

        micro_var = 0.0
        if len(self._nose_x_history) > 1:
            vx = float(np.var(self._nose_x_history))
            vy = float(np.var(self._nose_y_history))
            # Normalise: MICRO_MOVE_HIGH ≈ "very high" variance
            micro_var = min((vx + vy) / (2.0 * cfg.MICRO_MOVE_HIGH), 1.0)

        # ── Confusion score ───────────────────────────────────────────────────
        result.confusion_score = self._confusion.compute(
            blinks_per_minute   = self._ear.blinks_per_minute,
            head_angle_variance = self._head.angle_variance,
            gaze_loss           = self._gaze.gaze_loss_score(),
            micro_movement      = micro_var,
        )

        # ── Engagement score ──────────────────────────────────────────────────
        result.engagement_score = self._engagement.compute(
            ear_normalised  = self._ear.normalised_ear(),
            head_stability  = self._head.normalised_stability(),
            contact_ratio   = self._gaze.contact_ratio,
            confusion_score = result.confusion_score,
        )

        # ── CSV logging ───────────────────────────────────────────────────────
        if self._logger and self._frame_number % cfg.LOG_INTERVAL_FRAMES == 0:
            self._logger.write_row(
                frame_number      = self._frame_number,
                sleep_state       = result.is_sleeping,
                tilt_state        = result.is_tilted,
                tilt_angle_deg    = result.tilt_angle_deg,
                blink_count       = result.blink_count,
                blinks_per_minute = result.blinks_per_minute,
                eye_contact       = result.eye_contact,
                engagement_score  = result.engagement_score,
                confusion_score   = result.confusion_score,
                head_nod          = result.head_nod,
                head_shake        = result.head_shake,
                ear_left          = result.ear_left,
                ear_right         = result.ear_right,
                ear_avg           = result.ear_avg,
            )

        return result

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Release MediaPipe resources and close logger."""
        self._landmarker.close()
        if self._logger:
            self._logger.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
