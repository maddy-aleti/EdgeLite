"""
landmarks.py
─────────────────────────────────────────────────────────────────────────────
MediaPipe Face Landmarker index constants and low-level geometry helpers.

Why constants here?
  Landmark indices are magic numbers scattered throughout MediaPipe docs.
  Centralising them means a single place to update if the model version changes
  and makes every caller self-documenting.

CPU / memory impact:
  All functions are pure numpy — no Python-level loops over landmarks.
  Each function allocates at most one or two tiny intermediate arrays.
  Cost is negligible compared to model inference.
"""

import math
import numpy as np


# ─── MediaPipe Face Landmarker — 478 landmark indices ────────────────────────
# The task model uses 478 points: 468 face mesh + 10 iris points.

# Six-point eye model for EAR computation
#   p1 = outer corner, p4 = inner corner  (horizontal axis)
#   p2, p3 = top lid points
#   p5, p6 = bottom lid points
LEFT_EYE_EAR  = [33, 160, 158, 133, 153, 144]   # [p1, p2, p3, p4, p5, p6]
RIGHT_EYE_EAR = [362, 385, 387, 263, 373, 380]  # [p1, p2, p3, p4, p5, p6]

# Eye corner landmarks used for head-tilt angle
LEFT_EYE_OUTER  = 33
RIGHT_EYE_OUTER = 263

# Iris centres (only present when iris tracking enabled in task model)
LEFT_IRIS_CENTER  = 468
RIGHT_IRIS_CENTER = 473

# Nose landmarks
NOSE_TIP    = 4      # Front-most nose point
NOSE_BRIDGE = 6      # Between eyes, used for face-center reference

# Mouth corners (used for mouth state / optional smile detection)
MOUTH_LEFT  = 61
MOUTH_RIGHT = 291

# Face bounding landmarks (top / bottom / sides)
FOREHEAD    = 10
CHIN        = 152
LEFT_CHEEK  = 234
RIGHT_CHEEK = 454

# Full lists for face bounding box computation (convex hull approximation)
FACE_BOUNDARY = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
                 361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
                 176, 149, 150, 136, 172, 58,  132, 93,  234, 127,
                 162, 21,  54,  103, 67,  109]

# Left / right eye full outlines (for visualisation)
LEFT_EYE_OUTLINE  = [33, 7, 163, 144, 145, 153, 154, 155, 133,
                     173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE_OUTLINE = [362, 382, 381, 380, 374, 373, 390, 249, 263,
                     466, 388, 387, 386, 385, 384, 398]


# ─── Geometry helpers ─────────────────────────────────────────────────────────

def euclidean(p1: np.ndarray, p2: np.ndarray) -> float:
    """
    Euclidean distance between two 2-D points.
    Operates on numpy arrays of shape (2,) — avoids Python sqrt overhead
    for the 3-D case we don't need.
    """
    d = p1 - p2
    return math.sqrt(float(d[0] * d[0] + d[1] * d[1]))


def eye_aspect_ratio(lm_xy: np.ndarray, indices: list) -> float:
    """
    Compute Eye Aspect Ratio (EAR) from six landmark (x, y) coordinates.

    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    Args:
        lm_xy   : float32 array of shape (N, 2) — all (x, y) landmarks
        indices : 6-element list [p1, p2, p3, p4, p5, p6]

    Returns:
        EAR value in [0, ~0.4]; lower = more closed.

    CPU note: 3 euclidean calls + 2 additions — effectively free.
    """
    p = lm_xy[indices]           # shape (6, 2)
    vertical_a = euclidean(p[1], p[5])   # p2 – p6
    vertical_b = euclidean(p[2], p[4])   # p3 – p5
    horizontal = euclidean(p[0], p[3])   # p1 – p4
    if horizontal < 1e-6:
        return 0.0
    return (vertical_a + vertical_b) / (2.0 * horizontal)


def eye_tilt_angle(lm_xy: np.ndarray) -> float:
    """
    Compute head roll angle (degrees) from the eye-corner line.

    Uses LEFT_EYE_OUTER → RIGHT_EYE_OUTER vector.
    Positive angle = head tilted right; negative = tilted left.

    CPU note: one atan2 call — negligible.
    """
    left  = lm_xy[LEFT_EYE_OUTER]
    right = lm_xy[RIGHT_EYE_OUTER]
    dx = float(right[0] - left[0])
    dy = float(right[1] - left[1])
    angle_rad = math.atan2(dy, dx)
    return math.degrees(angle_rad)


def nose_face_deviation(lm_xy: np.ndarray) -> float:
    """
    Normalised horizontal deviation of nose tip from face centre.

    Returns a value in ~[-0.5, 0.5]:
      ~0   → facing straight ahead
      ±0.1+ → noticeable lateral gaze / yaw

    CPU note: two index lookups and one subtraction.
    """
    nose_x  = float(lm_xy[NOSE_TIP][0])
    left_x  = float(lm_xy[LEFT_CHEEK][0])
    right_x = float(lm_xy[RIGHT_CHEEK][0])
    face_width = right_x - left_x
    if face_width < 1e-6:
        return 0.0
    face_center_x = (left_x + right_x) / 2.0
    return (nose_x - face_center_x) / face_width


def nose_position_normalised(lm_xy: np.ndarray) -> tuple:
    """
    Returns (nx, ny) nose position normalised by face bounding box [0, 1].
    Used for micro-movement and gesture tracking.

    Output is relative to the face so head translation doesn't pollute signal.
    """
    left_x  = float(lm_xy[LEFT_CHEEK][0])
    right_x = float(lm_xy[RIGHT_CHEEK][0])
    top_y   = float(lm_xy[FOREHEAD][1])
    bot_y   = float(lm_xy[CHIN][1])

    face_w = max(right_x - left_x, 1e-6)
    face_h = max(bot_y   - top_y,  1e-6)

    nx = (float(lm_xy[NOSE_TIP][0]) - left_x) / face_w
    ny = (float(lm_xy[NOSE_TIP][1]) - top_y)  / face_h
    return nx, ny


def landmarks_to_xy(face_landmarks, img_w: int, img_h: int) -> np.ndarray:
    """
    Convert MediaPipe NormalizedLandmarkList to a float32 numpy array
    of pixel coordinates with shape (N, 2).

    Doing this conversion once per frame and passing the array to all modules
    avoids redundant attribute lookups inside tight loops.

    Args:
        face_landmarks : mediapipe face_landmarker FaceLandmarkerResult landmark list
        img_w, img_h   : frame dimensions in pixels

    Returns:
        np.ndarray of shape (N, 2), dtype float32
    """
    lm = face_landmarks
    coords = np.empty((len(lm), 2), dtype=np.float32)
    for i, pt in enumerate(lm):
        coords[i, 0] = pt.x * img_w
        coords[i, 1] = pt.y * img_h
    return coords
