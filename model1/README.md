# Edge AI Classroom Engagement Monitor

Real-time, CPU-only, offline student engagement monitoring pipeline powered by MediaPipe Face Landmarker.

---

## Architecture

```
model/
├── config.py         ← All thresholds / weights (tune here, nowhere else)
├── landmarks.py      ← MediaPipe index constants + geometry helpers
├── ear_detector.py   ← EAR formula → blink rate + sleep detection
├── head_pose.py      ← Eye-line angle → tilt state + variance
├── eye_contact.py    ← Nose deviation → gaze/contact ratio
├── confusion.py      ← Weighted confusion score [0-100]
├── engagement.py     ← Weighted engagement score [0-100]
├── gesture.py        ← Head nod / shake via oscillation counting
├── logger.py         ← CSV session logger
├── pipeline.py       ← Orchestrator: frame → EngagementResult
├── main.py           ← Webcam entry point (run this)
├── requirements.txt
└── logs/             ← Auto-created; CSV files saved here
```

> **MediaPipe task model NOT included** — download separately (see Setup).

---

## Setup

### 1. Install dependencies
```bash
pip install -r model/requirements.txt
```

### 2. Download the MediaPipe Face Landmarker model
```bash
# From the EdgeLite/ root or model/ directory:
curl -L -o model/face_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
```
Or download manually from:  
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

The file is ~10 MB. Place it at `model/face_landmarker.task` (matches `MODEL_PATH` in `config.py`).

---

## Run

```bash
# From the EdgeLite/ directory:
python model/main.py

# Options
python model/main.py --cam 1          # alternate webcam
python model/main.py --no-log         # disable CSV output
python model/main.py --no-display     # headless mode (prints to terminal)
python model/main.py --width 1280 --height 720
```

Press `Q` or `ESC` to quit.

---

## What it detects

| Metric | Method | Output |
|---|---|---|
| **Sleep** | EAR < 0.18 for 5 s | `is_sleeping` bool |
| **Head Tilt** | Eye-line angle > 15° for 3 s | `is_tilted` bool |
| **Eye Contact** | Nose deviation from face center | `eye_contact` bool + `contact_ratio` [0-1] |
| **Blink Rate** | EAR dip detection → blinks/min | `blinks_per_minute` float |
| **Confusion** | Weighted: blink rate + head variance + gaze + micro-movement | `confusion_score` [0-100] |
| **Engagement** | Weighted: EAR + head stability + contact − confusion penalty | `engagement_score` [0-100] |
| **Head Nod** | Vertical nose oscillation ≥ 2 cycles | `head_nod` bool |
| **Head Shake** | Horizontal nose oscillation ≥ 2 cycles | `head_shake` bool |

---

## CSV Log Format

Saved to `model/logs/session_<timestamp>.csv`:

```
timestamp, frame_number, sleep_state, tilt_state, tilt_angle_deg,
blink_count, blinks_per_minute, eye_contact, engagement_score,
confusion_score, head_nod, head_shake, ear_left, ear_right, ear_avg
```

One row written every 30 frames (~1 s at 30 FPS).

---

## Performance

| Metric | Target | Typical (modern CPU) |
|---|---|---|
| Inference | < 40 ms | 15–25 ms |
| FPS | > 20 | 25–30 |
| RAM | < 300 MB | ~100–130 MB |
| GPU | None required | — |

---

## Tuning

All thresholds live in `config.py`. Key values to adjust for your environment:

```python
EAR_THRESHOLD        = 0.21   # Lower for students with smaller eye openings
TILT_THRESHOLD_DEG   = 15.0   # Raise to allow more casual head positions
BLINK_RATE_HIGH      = 25     # blinks/min above this triggers confusion signal
EYE_CONTACT_NOSE_TOLERANCE = 0.04   # Raise if students sit far from camera
```

---

## Design Philosophy

- **No GPU required** — all inference on CPU
- **No cloud** — fully offline
- **Geometry over deep learning** — EAR/angles are explainable and auditable
- **Preallocated buffers** — `collections.deque(maxlen=N)` prevents memory growth
- **Single model load** — MediaPipe loaded once in `pipeline.py __init__`
- **Modular** — each concern is its own class; swap any module independently
