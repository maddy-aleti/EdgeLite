# EdgeLite – Edge AI Engagement Monitor & Model Optimizer

A comprehensive edge AI suite for **real-time student engagement monitoring** and **PyTorch model optimization**. Built with on-device inference (MediaPipe, no cloud), MJPEG video streaming, and a modern React dashboard.

---

## 🎯 Features

### 📊 **Student Engagement Analyzer**
- **Real-time engagement metrics** via on-device MediaPipe processing
- **Eye tracking** – EAR (Eye Aspect Ratio), eye contact, blink detection
- **Head pose analysis** – tilt angle, head nods, head shakes
- **Engagement scoring** – attention level and confusion detection
- **Live MJPEG video feed** with annotated frame from backend
- **Interactive dashboard** with timeline charts, pie charts, and bar charts
- **Session reports** – aggregated metrics over time
- **3-second polling** to balance performance and data freshness
- **CSV logging** – 1 entry every 3 seconds (90 frames @ 30fps)

### ⚡ **Model Optimizer**
- **PyTorch to ONNX conversion**
- **Quantization** for edge devices
- **Model compression** pipeline
- **Upload & download optimized models**

### 🏗️ **Architecture**
- **Backend APIs** – FastAPI services for engagement monitoring and optimization
- **Frontend Dashboard** – React + Vite with real-time metrics visualization
- **CORS-enabled** for local development
- **Offline-first** design – all processing happens on-device

---

## 📦 Project Structure

```
EdgeLite/
├── frontend/                      # React + Vite dashboard
│   ├── src/
│   │   ├── App.jsx               # Main app with navigation
│   │   ├── components/
│   │   │   ├── EngagementAnalyzer.jsx    # Real-time engagement UI
│   │   │   ├── ModelOptimizer.jsx        # Model optimization UI
│   │   │   ├── FileUpload.jsx
│   │   │   └── OptimizationMetrics.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── model1/                        # Engagement monitoring backend
│   ├── api_server.py             # FastAPI server (port 8001)
│   ├── pipeline.py               # EngagementPipeline class
│   ├── config.py                 # Configuration (camera, FPS, paths)
│   ├── ear_detector.py           # Eye Aspect Ratio detection
│   ├── eye_contact.py            # Eye contact tracking
│   ├── engagement.py             # Engagement scoring
│   ├── confusion.py              # Confusion detection
│   ├── gesture.py                # Gesture recognition
│   ├── head_pose.py              # Head pose estimation
│   ├── logger.py                 # CSV logging
│   ├── requirements.txt
│   ├── face_landmarker.task      # MediaPipe model
│   └── logs/                     # CSV session logs
│
├── optimization-service/          # Model optimization backend
│   ├── main.py                   # FastAPI server (port 8000)
│   ├── optimizer.py              # ONNX conversion & quantization
│   ├── requirements.txt
│   ├── uploads/                  # Input PyTorch models
│   └── optimized/                # Output ONNX models
│
├── edgeopt-backend/              # Node.js backend
│   ├── server.js                 # Express server (port 5000)
│   ├── package.json
│   ├── controllers/
│   ├── middleware/
│   ├── routes/
│   └── models/
│
├── sample_8mb_model.pt           # Sample PyTorch model
├── sample_128mb_model.pt          # Large sample model
├── generate_model.py             # Script to generate test models
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (for backends)
- **Node.js 16+** (for frontend & edgeopt-backend)
- **Webcam** (for engagement monitoring)

### 1️⃣ Setup & Run Engagement Analyzer Backend

```bash
cd model1
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn api_server:app --host 0.0.0.0 --port 8001
```

The backend will:
- Open your webcam
- Run MediaPipe face detection
- Stream MJPEG video to `/video_feed`
- Expose metrics on `/metrics`
- Log session data to `logs/session_*.csv`

**Endpoints:**
- `POST /session/start` – Start monitoring
- `POST /session/stop` – Stop monitoring
- `GET /metrics` – Get all metrics (JSON)
- `GET /video_feed` – MJPEG stream
- `GET /session/status` – Session status

### 2️⃣ Setup & Run Frontend Dashboard

```bash
cd frontend
npm install
npm start
```

Opens at [http://localhost:5173](http://localhost:5173)

**Features:**
- Start/stop engagement capture
- Live video feed + real-time metrics
- Timeline charts (engagement over time)
- Pie chart (attention distribution)
- Bar chart (score breakdown)
- Detailed signals (eye metrics, head gestures)
- Session reports

### 3️⃣ (Optional) Model Optimization Service

```bash
cd optimization-service
python -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or:
```bash
cd edgeopt-backend
npm install
npm start
```

---

## 📊 Dashboard Views

### **Live Dashboard**
- Real-time video feed with MJPEG stream
- Engagement/Confusion scores with progress bars
- Eye attention metrics (EAR, eye contact, blinking)
- Head pose data (tilt, nods, shakes)
- Blink activity counter
- System performance stats (FPS, inference time, frame count)
- Real-time engagement timeline
- State distribution pie chart
- Score breakdown bar chart

### **Detailed Signals**
- Eye metrics panel (EAR left/right, eye contact ratio, blinking, sleeping)
- Head & gesture panel (tilt angle, head nodes, shakes, blink count)

### **Session Report**
- Aggregated statistics (samples collected, avg engagement, avg confusion)
- Historical timeline visualization

### **System Metrics**
- FPS, Inference time, Frames processed
- Face detection status
- Pipeline health

---

## 🔧 Configuration

Edit [model1/config.py](model1/config.py) to customize:

```python
CAMERA_INDEX = 0                  # Webcam index
FRAME_WIDTH = 640                 # Resolution
FRAME_HEIGHT = 480
TARGET_FPS = 30                   # Target frame rate

LOG_INTERVAL_FRAMES = 90          # CSV log every ~3 seconds
LOG_DIR = "logs"
LOG_FILENAME = "session_log.csv"

# Gesture detection thresholds
GESTURE_DEADZONE = 0.008
```

---

## 📈 How It Works

### **Engagement Pipeline** (model1/pipeline.py)

1. **Capture** – OpenCV reads webcam frames at 30fps
2. **Face Detection** – MediaPipe detects face landmarks (468 points)
3. **Extract Signals**:
   - Eye Aspect Ratio (EAR) → blinking & sleepiness
   - Eye contact → gaze direction
   - Head pose → tilt angle
   - Gestures → head nods, shakes
4. **Score** – Engagement & confusion metrics (0-100)
5. **Stream** – MJPEG encode & serve to frontend
6. **Log** – CSV entry every 3 seconds with all metrics

### **API Response** (/metrics)

```json
{
  "face_detected": true,
  "fps": 30.5,
  "inference_ms": 12.3,
  "frame_number": 1542,
  "ear_left": 0.25,
  "ear_right": 0.26,
  "ear_avg": 0.255,
  "is_blinking": false,
  "is_sleeping": false,
  "blink_count": 47,
  "blinks_per_minute": 15.7,
  "tilt_angle_deg": 5.2,
  "is_tilted": false,
  "eye_contact": true,
  "contact_ratio": 0.92,
  "engagement_score": 75.3,
  "confusion_score": 2.1,
  "head_nod": false,
  "head_shake": false
}
```

---

## 📝 Logging

Session data is logged to CSV every 3 seconds:

**File:** `model1/logs/session_YYYYMMDD_HHMMSS.csv`

**Columns:**
- timestamp, frame_number, sleep_state, tilt_state, tilt_angle_deg
- blink_count, blinks_per_minute, eye_contact, engagement_score, confusion_score
- head_nod, head_shake, ear_left, ear_right, ear_avg, contact_ratio

---

## 🎨 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts |
| **Engagement Backend** | FastAPI, OpenCV, MediaPipe, NumPy |
| **Optimization Backend** | FastAPI, ONNX, PyTorch |
| **Node Backend** | Express.js |
| **Streaming** | MJPEG over HTTP |
| **Logging** | CSV |

---

## 🔌 API Endpoints

### **Engagement Analyzer (Port 8001)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/session/start` | Start camera capture & pipeline |
| `POST` | `/session/stop` | Stop pipeline |
| `GET` | `/session/status` | Get session status |
| `GET` | `/metrics` | Get all metrics (JSON) |
| `GET` | `/video_feed` | MJPEG stream |

### **Model Optimizer (Port 8000)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/optimize` | Upload & optimize PyTorch model |

---

## 🐛 Troubleshooting

### **Camera Not Opening**
- Check `CAMERA_INDEX` in [config.py](model1/config.py)
- Grant webcam permissions

### **No Video Feed**
- Confirm api_server is running on port 8001
- Check CORS settings in api_server.py
- Ensure camera is not in use by another app

### **Slow Metrics Polling**
- Polling interval is 3000ms (3 seconds) – change in EngagementAnalyzer.jsx: `setInterval(poll, 3000)`
- CSV logs every 90 frames (~3s) – adjust `LOG_INTERVAL_FRAMES` in config.py

### **High Inference Time**
- Reduce `FRAME_WIDTH` and `FRAME_HEIGHT` in config.py
- Lower `TARGET_FPS`
- Check CPU/GPU usage

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| [api_server.py](model1/api_server.py) | FastAPI server with MJPEG streaming |
| [pipeline.py](model1/pipeline.py) | Main EngagementPipeline class |
| [config.py](model1/config.py) | Global configuration |
| [EngagementAnalyzer.jsx](frontend/src/components/EngagementAnalyzer.jsx) | React dashboard component |
| [ear_detector.py](model1/ear_detector.py) | Eye aspect ratio detection |
| [engagement.py](model1/engagement.py) | Engagement scoring algorithm |

---

## 🎓 Learning Resources

- **MediaPipe Face Landmarks**: [mediapipe.dev](https://developers.google.com/mediapipe)
- **Eye Aspect Ratio (EAR)**: Tereza Soukupová & Jan Čech, 2016
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Recharts**: [recharts.org](https://recharts.org)

---

## 📄 License

This project is part of the EdgeLite Hackathon. All code is provided as-is for educational and research purposes.

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review [model1/config.py](model1/config.py) for configuration details
3. Check api_server logs at port 8001
4. Ensure all Python dependencies are installed: `pip install -r requirements.txt`

---

**Built with ❤️ for edge AI engagement monitoring · No cloud, all local.**
