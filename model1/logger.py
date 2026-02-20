"""
logger.py
─────────────────────────────────────────────────────────────────────────────
CSV session logger — writes one row per LOG_INTERVAL_FRAMES frames.

FILE FORMAT:
  Header defined by config.CSV_COLUMNS.
  Each row represents a snapshot of all metrics at a given frame.
  The file is flushed periodically to avoid data loss on crash.

THREAD SAFETY:
  This logger is designed for single-threaded use (the main inference loop).
  If you add a multi-threaded capture pipeline later, wrap write_row() in a
  threading.Lock.

CPU / memory impact:
  csv.writer uses Python's built-in C module — very fast.
  File is opened once and kept open; no open/close overhead per row.
  Flush() is called every 30 rows (~1 s) — negligible I/O on any disk.
"""

import csv
import os
from datetime import datetime

import config as cfg


class SessionLogger:
    """
    Opens a CSV file on construction and writes rows via write_row().
    Call close() when the session ends.
    """

    def __init__(self, filename: str | None = None):
        """
        Args:
            filename: Optional override for the CSV file path.
                      Defaults to config.LOG_DIR/config.LOG_FILENAME.
        """
        os.makedirs(cfg.LOG_DIR, exist_ok=True)

        if filename is None:
            # Embed timestamp in filename so multiple sessions don't overwrite
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"session_{ts}.csv"
            self._filepath = os.path.join(cfg.LOG_DIR, fname)
        else:
            self._filepath = filename

        self._file = open(self._filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=cfg.CSV_COLUMNS)
        self._writer.writeheader()
        self._file.flush()

        self._row_count = 0
        print(f"[Logger] Session log → {self._filepath}")

    # ── Public API ────────────────────────────────────────────────────────────

    def write_row(
        self,
        frame_number: int,
        sleep_state: bool,
        tilt_state: bool,
        tilt_angle_deg: float,
        blink_count: int,
        blinks_per_minute: float,
        eye_contact: bool,
        engagement_score: float,
        confusion_score: float,
        head_nod: bool,
        head_shake: bool,
        ear_left: float,
        ear_right: float,
        ear_avg: float,
    ) -> None:
        """
        Write one data row.

        Call this on every frame but gate the actual write with
        (frame_number % LOG_INTERVAL_FRAMES == 0) in the caller to avoid
        disk-I/O build-up.
        """
        row = {
            "timestamp":         datetime.now().isoformat(timespec="milliseconds"),
            "frame_number":      frame_number,
            "sleep_state":       int(sleep_state),
            "tilt_state":        int(tilt_state),
            "tilt_angle_deg":    round(tilt_angle_deg, 2),
            "blink_count":       blink_count,
            "blinks_per_minute": round(blinks_per_minute, 1),
            "eye_contact":       int(eye_contact),
            "engagement_score":  round(engagement_score, 1),
            "confusion_score":   round(confusion_score, 1),
            "head_nod":          int(head_nod),
            "head_shake":        int(head_shake),
            "ear_left":          round(ear_left,  4),
            "ear_right":         round(ear_right, 4),
            "ear_avg":           round(ear_avg,   4),
        }
        self._writer.writerow(row)
        self._row_count += 1

        # Periodic flush — every 30 rows ≈ 1 s at 30 FPS
        if self._row_count % 30 == 0:
            self._file.flush()

    def close(self) -> None:
        """Flush and close the CSV file."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()
            print(f"[Logger] Session saved — {self._row_count} rows → {self._filepath}")

    def __del__(self):
        self.close()

    @property
    def filepath(self) -> str:
        return self._filepath
