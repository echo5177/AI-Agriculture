# AI-Agriculture (Smart Farm AI System - Rice Disease Detection)

English | [简体中文](./README.md)

This is an AI system prototype for smart agriculture, integrating a dual-model architecture of **rice leaf disease object detection (YOLO)** and **image classification**. The system provides a sleek Web dashboard supporting **mobile real-time camera capture recognition** and **local image upload diagnostics**.

## Core Highlights

- **🎯 Object Detection (YOLO)**: A disease detection model trained on YOLOv8 that accurately localizes multiple lesions on leaves and draws bounding boxes, supporting the identification of 8 types of rice diseases.
- **🔬 Dual-Model Architecture**: A lightweight classification model (fast screening on edge devices) + YOLO detection model (accurate localization on the cloud), demonstrating an edge-cloud collaborative design.
- **📱 Real-time Camera**: Supports calling the camera directly in the browser, periodically capturing frames and uploading them for AI inference to simulate real-time field monitoring.
- **🖥️ Custom Rice Dashboard**: A beautiful warm-toned cream-colored frontend interface displaying real-time environmental sensor data (mocked) and AI diagnostic history.
- **⚡ Pure Python Architecture**: No database or Rust environment configurations required; starts with one click locally on Windows.

## Quick Start (Windows)

1. **Environment Preparation**:
   Ensure Python 3.9+ is installed. It is recommended to create and activate a new virtual environment using Anaconda/Miniconda:
   ```bash
   conda create -n ai_agriculture python=3.9
   conda activate ai_agriculture
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the System**:
   Run the following command in the root directory:
   ```bash
   python -m ai_engine.main
   ```

4. **Access the System**:
   - **Main Dashboard**: [https://localhost:8000](https://localhost:8000)
   - **Mobile Access**: Please refer to the [Mobile Guide](#mobile-guide) below.

## Mobile Guide

Using this project on a mobile phone provides the most realistic "in-field real-time diagnosis" experience.

1. **Same Network**: Ensure your mobile phone and computer are connected to the **same Wi-Fi** network.
2. **Get Computer IP**:
   - Run `ipconfig` in the computer terminal.
   - Find the `IPv4 Address` under `Wireless LAN adapter Wi-Fi` (usually `192.168.x.x` or `10.x.x.x`).
3. **Mobile Access**:
   - Open your mobile browser (Chrome or Safari).
   - Enter: `https://YOUR_COMPUTER_IP:8000` (e.g. `https://192.168.1.10:8000`).
   - **Note**: Since local self-signed certificates are used, the browser may prompt "Connection is not secure". Click "Advanced" -> "Proceed to site (unsafe)".
4. **Real-time AI Diagnosis**:
   - Click the **"Live Camera PoC"** button on the homepage.
   - Click "Start Camera" in the pop-up window.
   - Click "Start Loop Capture". The captured frames will be transmitted back to the computer backend in real-time, and AI disease inference will be completed automatically.

## YOLO Model Training

This project uses [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) for rice leaf disease object detection training.

### Dataset

Training uses `RiceLeafAnnotatedDataset/`, containing annotated data for 8 classes of rice diseases:

| No. | Class Name | Chinese Name |
|-----|------------|--------------|
| 0 | Bacterial_Leaf_Blight | 白叶枯病 |
| 1 | Brown_Spot | 褐斑病 |
| 2 | HealthyLeaf | 健康叶片 |
| 3 | Leaf_Blast | 叶瘟病 |
| 4 | Leaf_Scald | 叶烫伤病 |
| 5 | Narrow_Brown_Leaf_Spot | 窄褐条斑病 |
| 6 | Neck_Blast | 颈瘟病 |
| 7 | Rice_Hispa | 稻潜叶虫 |

### Training Commands

```bash
# Fast test (5 epochs, verify if pipeline runs fine)
python scripts/train_yolo.py --epochs 5

# Standard training (25 epochs, default parameters)
python scripts/train_yolo.py

# Full training (using larger model + more epochs)
python scripts/train_yolo.py --model yolov8s.pt --epochs 50 --imgsz 640

# If GPU VRAM is insufficient, reduce batch size
python scripts/train_yolo.py --batch 8
```

After training, the best weights are saved in `runs/detect/train/weights/best.pt`. Copy it to the `models/` directory for deployment:

```bash
copy runs\detect\train\weights\best.pt models\yolov8_rice_leaf.pt
```

## Technical Architecture: BSR (Backend-Side Rendering)

The system adopts a **backend rendering** strategy to handle object detection results:

```
User upload / Camera capture → Backend YOLO inference → Backend draws bounding boxes → Image with boxes returned to frontend for display
```

- **Zero Frontend Modification**: Bounding boxes are drawn directly on the image by the Python backend. The frontend only needs to display a normal image.
- **Dual-Model Fault Tolerance**: YOLO detector loads with priority. If weight files are missing, it automatically downgrades to the traditional classifier.
- **What You See Is What You Get**: The image seen on the dashboard is the final detection result and can be screenshotted directly for reports.

## Directory Structure

- `ai_engine/`: Backend inference service logic (FastAPI + YOLO + BSR rendering).
- `frontend/rice/`: Frontend code, including the dashboard and camera capture page.
- `models/`: AI model weight files (`yolov8_rice_leaf.pt` + traditional classifier).
- `scripts/`: Training scripts, including `train_yolo.py` (YOLO object detection training).
- `RiceLeafAnnotatedDataset/`: Annotated dataset in YOLO format (train/valid/test).
- `local_data/`: Runtime local storage (uploaded images and JSON metadata).

## Demonstration Tips (Must See)
1. **After starting the service**, open `mobile_live_capture.html` on your computer or mobile phone first.
2. Click "Start Camera", then click "Start Loop Upload".
3. Then return to the main dashboard page, you will find the "Visual AI Feedback" panel refreshes in real-time with the image you just captured and its diagnostic result.
