"""
config.py
─────────────────────────────────────────────────────────────────────────────
Centralised configuration for all thresholds, timing windows, and score weights.

Changing a value here propagates instantly to every module — no hunting through
files to tune the system.

CPU / memory impact: Pure Python constants loaded once at import time.
Zero runtime overhead.
"""
import os
_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Camera ──────────────────────────────────────────────────────────────────
CAMERA_INDEX        = 0          # OpenCV camera index (0 = default webcam)
TARGET_FPS          = 30         # Desired capture frame-rate
FRAME_WIDTH         = 640        # Capture resolution — keep low for edge devices
FRAME_HEIGHT        = 480

# ─── MediaPipe Model ─────────────────────────────────────────────────────────
# Download from:
# https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
MODEL_PATH          = os.path.join(_DIR, "face_landmarker.task")
NUM_FACES           = 1          # Max faces to track simultaneously
MIN_FACE_CONFIDENCE = 0.5        # Detection confidence threshold
MIN_TRACKING_CONFIDENCE = 0.5   # Tracking confidence threshold

# ─── Temporal Smoothing ───────────────────────────────────────────────────────
# All rolling windows are expressed in FRAMES (not seconds).
# At 30 FPS:  30 frames ≈ 1 s,  150 frames ≈ 5 s
SMOOTHING_WINDOW    = 10         # Frames used for metric smoothing
BLINK_WINDOW        = 90         # Frames to count blinks in (~3 s at 30 FPS)
GESTURE_WINDOW      = 45         # Frames to look for a nod/shake (~1.5 s)
CONFUSION_WINDOW    = 60         # Frames for confusion variance window (~2 s)
ENGAGEMENT_WINDOW   = 30         # Frames for engagement rolling average

# ─── Eye Aspect Ratio (EAR) ───────────────────────────────────────────────────
EAR_THRESHOLD       = 0.21       # Below this → eye considered closed
EAR_CONSEC_FRAMES   = 3          # Consecutive closed frames to count as a blink
SLEEP_EAR_THRESHOLD = 0.18       # Tighter threshold for definite eye-closed state
SLEEP_CONSEC_FRAMES = 150        # ~5 s at 30 FPS of closed eyes → sleep alert

# ─── Head Tilt ────────────────────────────────────────────────────────────────
TILT_THRESHOLD_DEG  = 15.0       # Degrees off-level → distraction
TILT_CONSEC_FRAMES  = 90         # ~3 s of sustained tilt → alert

# ─── Eye Contact ─────────────────────────────────────────────────────────────
EYE_CONTACT_NOSE_TOLERANCE = 0.04   # Normalised nose deviation (0–1) allowed
                                     # before gaze is considered "off-screen"

# ─── Confusion Score ──────────────────────────────────────────────────────────
# Weights for combining sub-signals into confusion score (must sum to 1.0)
CONFUSION_WEIGHTS = {
    "blink_rate":       0.25,    # Rapid blinking signals cognitive load
    "head_variance":    0.30,    # Unstable head = confused searching
    "gaze_reduction":   0.25,    # Looking away = not following content
    "micro_movement":   0.20,    # Fidgeting / micro-movements
}

BLINK_RATE_HIGH     = 25         # blinks/min above this → high confusion signal
BLINK_RATE_LOW      = 8          # blinks/min below this → low confusion signal
HEAD_VAR_HIGH       = 0.0012     # Normalised head angle variance → high signal
MICRO_MOVE_HIGH     = 0.003      # Normalised nose position variance → high signal

# ─── Engagement Score ─────────────────────────────────────────────────────────
# Higher weight = stronger influence on final engagement score
ENGAGEMENT_WEIGHTS = {
    "eye_openness":     0.30,    # EAR normalised (open eyes = engaged)
    "head_stability":   0.25,    # Inverse head variance
    "eye_contact":      0.30,    # On-screen gaze ratio
    "confusion_penalty":0.15,    # Subtracted when confusion is high
}

# ─── Gesture Detection ───────────────────────────────────────────────────────
NOD_OSCILLATIONS    = 2          # Min vertical zero-crossings to confirm a nod
SHAKE_OSCILLATIONS  = 2          # Min horizontal zero-crossings to confirm a shake
GESTURE_DEADZONE    = 0.008      # Ignore tiny movements (normalised units)

# ─── CSV Logging ─────────────────────────────────────────────────────────────
LOG_DIR             = os.path.join(_DIR, "logs")
LOG_FILENAME        = "session_log.csv"   # Relative to LOG_DIR
LOG_INTERVAL_FRAMES = 30                  # Write one row every N frames (~1 s)

CSV_COLUMNS = [
    "timestamp",
    "frame_number",
    "sleep_state",
    "tilt_state",
    "tilt_angle_deg",
    "blink_count",
    "blinks_per_minute",
    "eye_contact",
    "engagement_score",
    "confusion_score",
    "head_nod",
    "head_shake",
    "ear_left",
    "ear_right",
    "ear_avg",
]

# ─── Display Overlay ─────────────────────────────────────────────────────────
OVERLAY_FONT_SCALE  = 0.55
OVERLAY_THICKNESS   = 1
OVERLAY_LINE_HEIGHT = 22         # Pixels between overlay text lines
DISPLAY_HEATMAP     = True       # Show engagement colour band on frame border

# Colour palette (BGR for OpenCV)
COLOUR = {
    "green":    (0,   230, 100),
    "yellow":   (0,   220, 255),
    "red":      (50,   50, 240),
    "cyan":     (220, 210,   0),
    "white":    (230, 230, 230),
    "grey":     (120, 120, 120),
    "bg":       (20,   20,  35),
}
