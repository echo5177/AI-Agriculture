# -*- coding: utf-8 -*-
"""
YoloDetector – Backend-Side Rendering (BSR) wrapper for YOLOv8.

This module loads a trained YOLOv8 model and exposes a simple
``predict_bytes`` interface that:
  1. Runs object detection on the input image.
  2. Draws bounding boxes + labels directly onto the image (BSR).
  3. Returns structured metadata compatible with the existing
     dashboard API (predicted_class, confidence, disease_rate …).

The annotated image bytes are also returned so that ``api.py`` can
persist them in place of the raw upload – the frontend will then
display a picture that already contains coloured detection boxes
without any client-side rendering logic.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class YoloDetector:
    """Thin wrapper around ``ultralytics.YOLO`` for rice-leaf disease detection."""

    def __init__(self, model_path: str, confidence_threshold: float = 0.25) -> None:
        from ultralytics import YOLO

        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold

        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO weights not found: {self.model_path}")

        self.model = YOLO(str(self.model_path))
        self.model_version = f"yolov8_rice_{self.model_path.stem}"
        self.class_names: list[str] = list(self.model.names.values())
        logger.info(
            "YoloDetector loaded: %s  (%d classes: %s)",
            self.model_path.name,
            len(self.class_names),
            ", ".join(self.class_names),
        )

    # ------------------------------------------------------------------
    # Public API – drop-in compatible with RiceLeafClassifier.predict_bytes
    # ------------------------------------------------------------------

    def predict_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        """Run detection and return a result dict + annotated image bytes.

        Returns
        -------
        dict with keys:
            predicted_class   – name of the highest-confidence detection
            confidence        – confidence of that detection
            model_version     – identifier string
            topk              – list of {predicted_class, confidence}
            metadata          – disease_rate, is_diseased, advice_code,
                                detections (raw list), annotated_bytes
        """
        # Decode image
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image bytes")

        # Run inference
        results = self.model.predict(
            source=img,
            conf=self.confidence_threshold,
            verbose=False,
        )
        result = results[0]

        # Extract detections
        detections: list[dict] = []
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "class": self.class_names[cls_id],
                    "confidence": round(conf, 4),
                    "bbox": [round(v, 1) for v in [x1, y1, x2, y2]],
                })

        # Sort by confidence descending
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        # Determine overall prediction
        if detections:
            top = detections[0]
            predicted_class = top["class"]
            confidence = top["confidence"]
        else:
            predicted_class = "HealthyLeaf"
            confidence = 0.60

        is_diseased = predicted_class != "HealthyLeaf"
        disease_count = sum(1 for d in detections if d["class"] != "HealthyLeaf")

        # Build topk (unique classes, highest confidence each)
        seen: dict[str, float] = {}
        for d in detections:
            if d["class"] not in seen or d["confidence"] > seen[d["class"]]:
                seen[d["class"]] = d["confidence"]
        topk = [
            {"predicted_class": cls, "confidence": round(c, 4)}
            for cls, c in sorted(seen.items(), key=lambda x: -x[1])
        ]

        # ---- Backend-Side Rendering (BSR) ----
        annotated_img = result.plot()  # Ultralytics draws boxes + labels
        _, annotated_buf = cv2.imencode(".jpg", annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        annotated_bytes = annotated_buf.tobytes()

        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "model_version": self.model_version,
            "topk": topk,
            "metadata": {
                "advice_code": "inspect_leaf" if is_diseased else "normal_monitoring",
                "disease_rate": round(disease_count / max(len(detections), 1), 4),
                "is_diseased": is_diseased,
                "detection_count": len(detections),
                "disease_spot_count": disease_count,
                "detections": detections,
            },
            "annotated_bytes": annotated_bytes,
        }
