"""
api_server.py
─────────────────────────────────────────────────────────────────────────────
FastAPI backend for the Edge AI Classroom Engagement Monitor.

Runs the full engagement pipeline (camera + MediaPipe + all detectors) in a
background thread, then exposes the latest metrics via HTTP routes so the
React dashboard can poll them in real-time.

Usage:
    # From EdgeLite/model1/ with venv activated:
    uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload

    # OR directly:
    python api_server.py

React dashboard polls:
    http://localhost:8001/metrics          ← all metrics at once
    http://localhost:8001/session/start    ← POST to start camera
    http://localhost:8001/session/stop     ← POST to stop camera

CORS is enabled for http://localhost:5173 (Vite default).
"""

import sys
import os
import threading
import time

import cv2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Resolve model1/ directory so imports work regardless of cwd ──────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import config as cfg
from pipeline import EngagementPipeline, EngagementResult


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Edge AI Engagement Monitor API",
    description="Real-time student engagement metrics from the on-device AI pipeline.",
    version="1.0.0",
)

# Allow requests from the React Vite dev server and any localhost port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Shared State ─────────────────────────────────────────────────────────────

class SharedState:
    """
    Thread-safe container for the latest EngagementResult.
    The background capture thread writes; FastAPI route handlers read.
    """
    def __init__(self):
        self._lock   = threading.Lock()
        self._result = EngagementResult()   # default "empty" result
        self.running = False
        self.error   = None

    def update(self, result: EngagementResult):
        with self._lock:
            self._result = result

    def get(self) -> EngagementResult:
        with self._lock:
            return self._result


state = SharedState()


# ─── Background Capture Thread ────────────────────────────────────────────────

_capture_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _capture_loop():
    """
    Background thread:  open camera → run pipeline → push result to SharedState.
    Stops when _stop_event is set or camera fails.
    """
    global state
    cap = cv2.VideoCapture(cfg.CAMERA_INDEX)
    if not cap.isOpened():
        state.error = f"Cannot open camera index {cfg.CAMERA_INDEX}"
        state.running = False
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  cfg.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, cfg.TARGET_FPS)

    try:
        with EngagementPipeline(log_csv=True) as pipeline:
            while not _stop_event.is_set():
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue
                result = pipeline.process_frame(frame)
                state.update(result)
    except Exception as e:
        state.error = str(e)
    finally:
        cap.release()
        state.running = False


def _start_capture():
    global _capture_thread, _stop_event
    if state.running:
        return
    _stop_event.clear()
    state.error   = None
    state.running = True
    _capture_thread = threading.Thread(target=_capture_loop, daemon=True)
    _capture_thread.start()


def _stop_capture():
    global _capture_thread
    _stop_event.set()
    if _capture_thread and _capture_thread.is_alive():
        _capture_thread.join(timeout=5)
    state.running = False


# ─── Pydantic response models ─────────────────────────────────────────────────

class StatusResponse(BaseModel):
    running:        bool
    face_detected:  bool
    fps:            float
    inference_ms:   float
    frame_number:   int
    error:          str | None


class AllMetricsResponse(BaseModel):
    # Session
    face_detected:     bool
    fps:               float
    inference_ms:      float
    frame_number:      int
    # EAR
    ear_left:          float
    ear_right:         float
    ear_avg:           float
    is_blinking:       bool
    is_sleeping:       bool
    # Blinks
    blink_count:       int
    blinks_per_minute: float
    # Head
    tilt_angle_deg:    float
    is_tilted:         bool
    # Gaze
    eye_contact:       bool
    contact_ratio:     float
    # Scores
    engagement_score:  float
    confusion_score:   float
    # Gestures
    head_nod:          bool
    head_shake:        bool


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 65:
        return "green"
    if score >= 35:
        return "yellow"
    return "red"


def _require_running():
    if not state.running:
        raise HTTPException(status_code=503, detail="Pipeline not running. POST /session/start first.")


# ─── Routes ───────────────────────────────────────────────────────────────────

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is up."""
    return {"status": "ok", "service": "Edge AI Engagement Monitor"}


# ── Session control ───────────────────────────────────────────────────────────

@app.post("/session/start", tags=["Session"])
def session_start():
    """Start the webcam capture and inference pipeline."""
    if state.running:
        return {"message": "Already running", "running": True}
    _start_capture()
    return {"message": "Pipeline started", "running": True}


@app.post("/session/stop", tags=["Session"])
def session_stop():
    """Stop the webcam capture and inference pipeline."""
    _stop_capture()
    return {"message": "Pipeline stopped", "running": False}


@app.get("/session/status", response_model=StatusResponse, tags=["Session"])
def session_status():
    """Current session status — running state, face detection, FPS."""
    r = state.get()
    return StatusResponse(
        running       = state.running,
        face_detected = r.face_detected,
        fps           = r.fps,
        inference_ms  = r.inference_ms,
        frame_number  = r.frame_number,
        error         = state.error,
    )


# ── All metrics (main dashboard route) ───────────────────────────────────────

@app.get("/metrics", response_model=AllMetricsResponse, tags=["Metrics"])
def all_metrics():
    """
    Return ALL metrics in a single call.
    This is the primary route for the React dashboard to poll.
    """
    _require_running()
    r = state.get()
    return AllMetricsResponse(
        face_detected     = r.face_detected,
        fps               = r.fps,
        inference_ms      = r.inference_ms,
        frame_number      = r.frame_number,
        ear_left          = r.ear_left,
        ear_right         = r.ear_right,
        ear_avg           = r.ear_avg,
        is_blinking       = r.is_blinking,
        is_sleeping       = r.is_sleeping,
        blink_count       = r.blink_count,
        blinks_per_minute = r.blinks_per_minute,
        tilt_angle_deg    = r.tilt_angle_deg,
        is_tilted         = r.is_tilted,
        eye_contact       = r.eye_contact,
        contact_ratio     = r.contact_ratio,
        engagement_score  = r.engagement_score,
        confusion_score   = r.confusion_score,
        head_nod          = r.head_nod,
        head_shake        = r.head_shake,
    )
# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Auto-start the pipeline when running directly
    _start_capture()
    uvicorn.run(app, host="0.0.0.0", port=8001)
