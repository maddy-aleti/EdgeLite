"""
main.py
─────────────────────────────────────────────────────────────────────────────
Entry point for the Edge AI Classroom Engagement Monitor.

Usage:
    python main.py                  # default webcam, logging enabled
    python main.py --no-log         # disable CSV logging
    python main.py --cam 1          # use webcam index 1
    python main.py --width 1280     # change capture resolution

Run from the EdgeLite/model/ directory or set MODEL_PATH in config.py.

OVERLAY LAYOUT:
  ┌─────────────────────────────────────────────────┐
  │  [LEFT PANEL]          [WEBCAM FRAME]           │
  │  Engagement: 78%                                │
  │  Confusion:  22%      <face with landmarks>     │
  │  Blinks/min: 14                                 │
  │  Eye Contact: YES                               │
  │  Head Tilt:   NO                                │
  │  Sleeping:    NO                                │
  │  FPS: 28.4  Inf: 18ms                           │
  │                                                 │
  │  [ALERT BANNER if sleeping / tilted / confused] │
  └─────────────────────────────────────────────────┘

CPU / memory impact:
  cv2.putText calls are C-level — fast.
  cv2.rectangle for the panel background: one call.
  No Python-level pixel iteration anywhere.
"""

import sys
import os
import argparse
import cv2
import numpy as np

# ── Add model/ dir to path so imports work regardless of cwd ─────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import config as cfg
from pipeline import EngagementPipeline, EngagementResult


# ─── CLI arguments ────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Edge AI Classroom Engagement Monitor")
    p.add_argument("--cam",     type=int,   default=cfg.CAMERA_INDEX,  help="Webcam index")
    p.add_argument("--width",   type=int,   default=cfg.FRAME_WIDTH,   help="Capture width")
    p.add_argument("--height",  type=int,   default=cfg.FRAME_HEIGHT,  help="Capture height")
    p.add_argument("--no-log",  action="store_true",                   help="Disable CSV logging")
    p.add_argument("--no-display", action="store_true",                help="Headless mode (no window)")
    return p.parse_args()


# ─── Overlay helpers ──────────────────────────────────────────────────────────

C = cfg.COLOUR   # shorthand

def _text(img, text, x, y, color=C["white"], scale=None, thickness=None):
    scale     = scale     or cfg.OVERLAY_FONT_SCALE
    thickness = thickness or cfg.OVERLAY_THICKNESS
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


def _score_color(score: float) -> tuple:
    """Return BGR color: green >65, yellow 35–65, red <35."""
    if score >= 65:
        return C["green"]
    if score >= 35:
        return C["yellow"]
    return C["red"]


def _draw_bar(img, x, y, w, h, fraction: float, color: tuple, bg=C["bg"]):
    """Draw a filled progress bar."""
    cv2.rectangle(img, (x, y), (x + w, y + h), bg, -1)
    filled = int(w * max(0.0, min(fraction, 1.0)))
    if filled > 0:
        cv2.rectangle(img, (x, y), (x + filled, y + h), color, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (60, 60, 80), 1)


def _draw_panel(frame: np.ndarray, result: EngagementResult) -> np.ndarray:
    """
    Composite a 220-pixel left info panel next to the camera frame.

    Returns a new array (panel | frame) without modifying the original.
    """
    h, fw = frame.shape[:2]
    panel_w = 230
    total_w = panel_w + fw

    canvas = np.zeros((h, total_w, 3), dtype=np.uint8)
    canvas[:, :fw] = frame
    # Panel background
    cv2.rectangle(canvas, (fw, 0), (total_w - 1, h - 1), (18, 22, 40), -1)
    cv2.line(canvas, (fw, 0), (fw, h), (50, 60, 90), 1)

    px = fw + 12   # panel text x
    y  = 30        # current y cursor
    lh = cfg.OVERLAY_LINE_HEIGHT

    # ── Title ────
    _text(canvas, "EDGE AI MONITOR", px, y, C["cyan"], 0.45, 1)
    y += lh

    if not result.face_detected:
        _text(canvas, "No face detected", px, y + 20, C["yellow"])
        return canvas

    # ── Engagement bar ────────────────────────────────────────────────────────
    y += 6
    eng = result.engagement_score
    eng_col = _score_color(eng)
    _text(canvas, f"ENGAGEMENT", px, y, C["grey"], 0.40, 1)
    y += 16
    _draw_bar(canvas, px, y, panel_w - 24, 14, eng / 100.0, eng_col)
    _text(canvas, f"{eng:.0f}%", px + panel_w - 50, y + 11, eng_col, 0.45, 1)
    y += 28

    # ── Confusion bar ─────────────────────────────────────────────────────────
    conf = result.confusion_score
    conf_col = _score_color(100 - conf)   # inverse: high confusion = red
    _text(canvas, f"CONFUSION", px, y, C["grey"], 0.40, 1)
    y += 16
    _draw_bar(canvas, px, y, panel_w - 24, 14, conf / 100.0, conf_col)
    _text(canvas, f"{conf:.0f}%", px + panel_w - 50, y + 11, conf_col, 0.45, 1)
    y += 30

    # ── Divider ───────────────────────────────────────────────────────────────
    cv2.line(canvas, (px, y), (total_w - 12, y), (40, 50, 70), 1)
    y += 12

    # ── Metrics ───────────────────────────────────────────────────────────────
    def metric_line(label, value, ok_val=True):
        nonlocal y
        col = C["green"] if ok_val else C["red"]
        _text(canvas, label, px, y, C["grey"], 0.38, 1)
        _text(canvas, str(value), px + 115, y, col, 0.42, 1)
        y += lh

    metric_line("EAR avg",      f"{result.ear_avg:.3f}",
                ok_val=result.ear_avg > cfg.EAR_THRESHOLD)
    metric_line("Blinks/min",   f"{result.blinks_per_minute:.1f}",
                ok_val=cfg.BLINK_RATE_LOW <= result.blinks_per_minute <= cfg.BLINK_RATE_HIGH)
    metric_line("Tilt angle",   f"{result.tilt_angle_deg:+.1f}°",
                ok_val=not result.is_tilted)
    metric_line("Eye contact",  "YES" if result.eye_contact else "NO",
                ok_val=result.eye_contact)
    metric_line("Sleeping",     "YES" if result.is_sleeping else "NO",
                ok_val=not result.is_sleeping)
    metric_line("Tilted",       "YES" if result.is_tilted  else "NO",
                ok_val=not result.is_tilted)

    y += 4
    cv2.line(canvas, (px, y), (total_w - 12, y), (40, 50, 70), 1)
    y += 12

    # ── Gestures ──────────────────────────────────────────────────────────────
    if result.head_nod:
        _text(canvas, "NOD DETECTED", px, y, C["cyan"], 0.50, 1)
        y += lh
    if result.head_shake:
        _text(canvas, "SHAKE DETECTED", px, y, C["yellow"], 0.50, 1)
        y += lh

    # ── System metrics ────────────────────────────────────────────────────────
    _text(canvas, f"FPS: {result.fps:.1f}  Inf: {result.inference_ms:.0f}ms",
          px, h - 30, C["grey"], 0.38, 1)
    _text(canvas, f"Frame #{result.frame_number}",
          px, h - 14, C["grey"], 0.35, 1)

    return canvas


def _draw_alerts(canvas: np.ndarray, result: EngagementResult) -> None:
    """Draw alert banners directly on the camera portion of the canvas."""
    alerts = []
    if result.is_sleeping:
        alerts.append(("SLEEP ALERT — Student may be asleep!", C["red"]))
    if result.is_tilted:
        alerts.append(("DISTRACTION ALERT — Sustained head tilt", C["yellow"]))
    if result.confusion_score > 60:
        alerts.append((f"CONFUSION SPIKE — {result.confusion_score:.0f}%   Consider recap", C["yellow"]))

    for i, (msg, color) in enumerate(alerts):
        y = 50 + i * 30
        # Semi-transparent background
        overlay = canvas.copy()
        cv2.rectangle(overlay, (10, y - 18), (canvas.shape[1] - 250, y + 6),
                      (15, 15, 35), -1)
        cv2.addWeighted(overlay, 0.7, canvas, 0.3, 0, canvas)
        _text(canvas, msg, 16, y, color, 0.52, 1)


def _engagement_border(canvas: np.ndarray, result: EngagementResult) -> None:
    """
    Draw a thin coloured border on the camera frame portion to indicate
    engagement level at a glance (green / yellow / red).
    Only drawn when face is detected.
    """
    if not cfg.DISPLAY_HEATMAP or not result.face_detected:
        return
    h = canvas.shape[0]
    fw = canvas.shape[1] - 230    # width of the camera portion
    color = _score_color(result.engagement_score)
    thickness = 4
    cv2.rectangle(canvas, (0, 0), (fw - 1, h - 1), color, thickness)


# ─── Main loop ────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Open webcam
    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {args.cam}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, cfg.TARGET_FPS)

    print(f"[Camera] Opened — {int(cap.get(3))}×{int(cap.get(4))} @ {cfg.TARGET_FPS} FPS target")
    print("Press  Q  to quit\n")

    with EngagementPipeline(log_csv=not args.no_log) as pipeline:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[WARN] Empty frame received — retrying…")
                continue

            # ── Run all inference ─────────────────────────────────────────────
            result: EngagementResult = pipeline.process_frame(frame)

            # ── Build display ─────────────────────────────────────────────────
            if not args.no_display:
                display = _draw_panel(frame, result)
                _engagement_border(display, result)
                _draw_alerts(display, result)

                cv2.imshow("Edge AI Engagement Monitor", display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:   # Q or ESC
                    break
            else:
                # Headless: print summary every 30 frames
                if result.frame_number % 30 == 0:
                    print(
                        f"Frame {result.frame_number:5d} | "
                        f"FPS {result.fps:5.1f} | "
                        f"Eng {result.engagement_score:5.1f}% | "
                        f"Conf {result.confusion_score:5.1f}% | "
                        f"Sleep {result.is_sleeping} | "
                        f"Tilt {result.is_tilted}"
                    )

    cap.release()
    if not args.no_display:
        cv2.destroyAllWindows()
    print("\n[Done] Session ended.")


if __name__ == "__main__":
    main()
