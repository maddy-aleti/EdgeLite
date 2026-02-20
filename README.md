# 🚀 EdgeLite
**Edge Model Optimization & Deployment Platform for Low-Resource Environments**

---

## 📌 Overview

EdgeLite is a developer-focused edge AI optimization and deployment platform that enables machine learning models to run efficiently on CPU-only edge devices.

We demonstrate the effectiveness of our optimization engine through a real-world deployment use case:

🎓 A **Real-Time Student Engagement Monitoring System** running entirely offline on CPU.

EdgeLite solves a fundamental challenge in modern AI systems:

> **How do we deploy heavy deep learning models on low-resource edge devices without sacrificing performance?**

---

## 🎯 Problem Statement

Modern ML/DL models are:
- Large (50–200 MB)
- GPU-dependent
- High latency on CPUs
- Cloud-dependent
- Resource intensive

This makes deployment difficult in:
- Classrooms
- Rural institutions
- Low-cost devices
- Privacy-sensitive environments
- Offline systems

EdgeLite addresses this by providing:

✔ Model optimization pipeline  
✔ Edge deployment readiness  
✔ Performance benchmarking  
✔ Real-world validation  

---

## 🏗 System Architecture

EdgeLite consists of two major layers:

### 1️⃣ Edge Optimization Engine (Core Innovation)

A model transformation pipeline that enables deployment on low-resource hardware.

| Stage | Description |
|---|---|
| **Input** | PyTorch / ONNX / TensorFlow model (heavy FP32) |
| **Quantization** | FP32 → INT8 weight compression |
| **Pruning** | Remove redundant parameters |
| **Format Conversion** | Export to ONNX / TFLite |
| **Benchmarking** | Latency + memory comparison |
| **Output** | Optimized model + performance report |

### 2️⃣ Edge Deployment Use Case (Demonstration Layer)

To validate our platform, we built a:

🎓 **Real-Time Student Engagement Analyzer** — a CPU-only engagement monitoring system that:

- Uses **MediaPipe Face Landmarker**
- Extracts **468 facial landmarks** per frame
- Computes:
  - Eye Aspect Ratio (EAR) & blink rate
  - Head tilt angle
  - Eye contact score
  - Confusion score
  - Engagement score
- Runs at **~30 FPS**
- Average inference time: **~8 ms**
- Requires **no GPU**
- Works **fully offline**
- Does **not** store video data

---

## 📂 Project Structure

```
EdgeLite/
│
├── model1/                   # Real-time engagement engine (Python + MediaPipe + FastAPI)
│   ├── api_server.py         # FastAPI backend — exposes metrics over HTTP (port 8001)
│   ├── main.py               # Standalone OpenCV webcam runner
│   ├── pipeline.py           # Master orchestrator (EngagementPipeline)
│   ├── ear_detector.py       # Eye Aspect Ratio + blink/sleep detection
│   ├── head_pose.py          # Head tilt angle detection
│   ├── eye_contact.py        # Gaze / nose-deviation tracking
│   ├── confusion.py          # Weighted confusion score
│   ├── engagement.py         # Weighted engagement score
│   ├── gesture.py            # Head nod / shake detection
│   ├── landmarks.py          # MediaPipe landmark index constants & geometry helpers
│   ├── logger.py             # CSV session logger
│   ├── config.py             # All thresholds, weights, and window sizes
│   └── requirements.txt
│
├── optimization-service/     # Model optimization pipeline (Python + FastAPI)
│   ├── main.py               # FastAPI upload → optimize → download endpoint
│   ├── optimizer.py          # Quantization, pruning, ONNX/TFLite conversion
│   └── requirements.txt
│
├── edgeopt-backend/          # Node.js/Express API server (port 5000, MongoDB)
│   ├── server.js
│   ├── routes/
│   ├── controllers/
│   ├── models/
│   ├── middleware/
│   └── config/
│
├── frontend/                 # React dashboard UI (Vite + Tailwind CSS)
│   ├── src/
│   ├── index.html
│   └── vite.config.js
│
└── README.md
```

---

## ⚙️ Key Features

### 🔬 Optimization Engine
- Lightweight conversion pipeline
- Quantization support (FP32 → INT8)
- Performance benchmarking
- Deployment-ready export
- Framework flexibility (extensible)

### 🎓 Engagement Analyzer
- CPU-only inference
- Real-time (20–30 FPS)
- Geometry-based explainable AI
- Temporal smoothing on all signals
- Offline-first design
- CSV session logging

### 🌐 Developer Platform
- Upload heavy model → optimize automatically
- Compare before/after metrics
- Deploy to edge

---

## 📊 Performance Benchmarks (Engagement Engine)

| Metric | Value |
|---|---|
| FPS | ~29–30 |
| Avg Inference Time | ~8 ms |
| RAM Usage | < 300 MB |
| GPU Required | ❌ No |
| Internet Required | ❌ No |

---

## 🔒 Security & Privacy

EdgeLite is designed with **privacy-first** principles:

- No video data stored
- No cloud transmission required
- All inference runs locally on device
- Logs contain only behavioral metrics (CSV)
- No identity tracking

---

## 🧪 Testing Strategy

- Real-time performance testing (~10 min runtime stability)
- Low-light and face-absence handling
- Modular unit tests for core signal functions
- Stress test over extended sessions

---

## 🚀 Deployment

### Engagement Engine (Python + FastAPI)
```bash
cd model1
pip install -r requirements.txt

# Run standalone with OpenCV window
python main.py

# Run as API server (Swagger at http://localhost:8001/docs)
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

### Optimization Service (Python + FastAPI)
```bash
cd optimization-service
pip install -r requirements.txt
python main.py
# Run as API server (Swagger at http://localhost:8001/docs)
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```
```

### Backend (Node.js + Express + MongoDB)
```bash
cd edgeopt-backend
npm install
node server.js
```

### Frontend (React + Vite + Tailwind)
```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Target Applications

Although demonstrated with classroom engagement monitoring, EdgeLite is adaptable to:

- Healthcare edge AI
- Retail analytics
- Surveillance systems
- Agriculture monitoring
- Industrial quality control
- Driver monitoring systems

---

## 💡 Why EdgeLite?

EdgeLite bridges the gap between:

**Heavy AI research models** → **Practical edge deployment**

It enables developers to:
- Optimize models with minimal effort
- Measure real performance gains (latency, memory, FPS)
- Deploy confidently on CPU-only devices
- Prove effectiveness through a live real-world use case

---

## 🏆 Hackathon Value Proposition

| Dimension | Weight |
|---|---|
| Research (Optimization pipeline) | 33% |
| Product (Developer platform) | 33% |
| Social Impact (Education analytics) | 33% |
| **Edge-focused throughout** | **100%** |

---

## 📌 Future Improvements

- Multi-user engagement tracking
- Automated pruning selection
- Model accuracy validation after optimization
- Adaptive threshold calibration
- Raspberry Pi deployment benchmarking

---

## 👨‍💻 Team Vision

We aim to make AI truly deployable in low-resource environments by combining:

- Model compression techniques
- Edge-first architecture
- Real-world validation
- Developer tooling

---

> **EdgeLite** — Making AI Lightweight, Deployable, and Practical.

