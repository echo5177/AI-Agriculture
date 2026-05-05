from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, Query, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Any, Literal
import uuid
import os
import shutil
import random
from datetime import datetime, timedelta

# ------------------------------------------------------------------
# 1. Internal Logic & Schemas (Moved from common)
# ------------------------------------------------------------------

class ImageLoadError(ValueError):
    """Raised when image bytes cannot be decoded."""

def detect_image_kind(image_bytes: bytes) -> str | None:
    if image_bytes.startswith(b"\xff\xd8\xff"): return "jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")): return "gif"
    if image_bytes.startswith(b"BM"): return "bmp"
    return None

def validate_image_bytes(image_bytes: bytes) -> str:
    if not image_bytes: raise ImageLoadError("empty image bytes")
    kind = detect_image_kind(image_bytes)
    if kind is None: raise ImageLoadError("unsupported or invalid image bytes")
    return kind

class TopKItem(BaseModel):
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)

class PredictionResponse(BaseModel):
    status: str = "success"
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    topk: list[TopKItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"protected_namespaces": ()}

# ------------------------------------------------------------------
# 2. Router & State
# ------------------------------------------------------------------

router = APIRouter()
_classifier = None

def set_classifier(classifier) -> None:
    global _classifier
    _classifier = classifier

def _predict(image_bytes: bytes) -> PredictionResponse:
    validate_image_bytes(image_bytes)
    if _classifier is not None:
        raw = _classifier.predict_bytes(image_bytes)
    else:
        # Mock prediction if model is not loaded
        raw = {
            "predicted_class": "Healthy",
            "confidence": 0.82,
            "model_version": "rice_mock_v0",
            "topk": [{"predicted_class": "Healthy", "confidence": 0.82}],
            "metadata": {"advice_code": "normal_monitoring", "disease_rate": 0.12, "is_diseased": False},
        }
    return PredictionResponse(
        predicted_class=raw["predicted_class"],
        confidence=raw["confidence"],
        model_version=raw["model_version"],
        topk=raw.get("topk", []),
        metadata=raw.get("metadata", {}),
    )

# ------------------------------------------------------------------
# 3. Core API Endpoints
# ------------------------------------------------------------------

UPLOAD_DIR = "local_data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/image/upload")
async def upload_image(
    file: UploadFile = File(...),
    device_id: str = Query(...),
    ts: str = Query(None)
):
    """Handle image upload, store locally, and run inference."""
    try:
        upload_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        file_path = os.path.join(UPLOAD_DIR, f"{upload_id}{ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        
        prediction = _predict(image_bytes)
        
        # Persistence
        meta_path = os.path.join(UPLOAD_DIR, f"{upload_id}.json")
        import json
        with open(meta_path, "w", encoding="utf-8") as fmeta:
            json.dump({
                "predicted_class": prediction.predicted_class,
                "confidence": prediction.confidence,
                "disease_rate": prediction.metadata.get("disease_rate", 0.0),
                "captured_at": ts or datetime.utcnow().isoformat() + "Z"
            }, fmeta)

        return {
            "status": "success",
            "upload_id": upload_id,
            "predicted_class": prediction.predicted_class,
            "confidence": prediction.confidence,
            "disease_rate": prediction.metadata.get("disease_rate", 0.0),
            "captured_at": ts or datetime.utcnow().isoformat() + "Z",
            "upload_status": "inferred"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/image/file")
async def get_image_file(upload_id: str = Query(None), saved_path: str = Query(None)):
    if upload_id:
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(upload_id) and not f.endswith(".json"):
                return FileResponse(os.path.join(UPLOAD_DIR, f))
    if saved_path and os.path.exists(saved_path):
        return FileResponse(saved_path)
    raise HTTPException(status_code=404, detail="Image not found")

@router.get("/image/uploads")
async def get_image_uploads(limit: int = 10):
    uploads = []
    if os.path.exists(UPLOAD_DIR):
        import json
        files = [f for f in os.listdir(UPLOAD_DIR) if not f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)), reverse=True)
        for f in files[:limit]:
            uid = os.path.splitext(f)[0]
            mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(UPLOAD_DIR, f)))
            meta_path = os.path.join(UPLOAD_DIR, f"{uid}.json")
            real_meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fm:
                        real_meta = json.load(fm)
                except: pass

            uploads.append({
                "upload_id": uid,
                "device_id": "MOBILE-CAM",
                "captured_at": real_meta.get("captured_at") or mtime.isoformat() + "Z",
                "upload_status": "inferred",
                "predicted_class": real_meta.get("predicted_class") or "Healthy",
                "disease_rate": real_meta.get("disease_rate") or 0.1
            })
    return uploads

# ------------------------------------------------------------------
# 4. Mock & Helper Endpoints (Merged from common)
# ------------------------------------------------------------------

DEVICES = [
    {"device_id": "NODE-01-RICE", "location": "North Terrace", "crop_type": "Rice", "farm_note": "AIT103 Field", "sensors": ["dht22", "soil_modbus_02"]},
    {"device_id": "MOBILE-CAM", "location": "Field Office", "crop_type": "Rice", "farm_note": "Mobile Unit", "sensors": ["system"]},
]

@router.get("/devices")
async def get_devices(): return {"devices": DEVICES}

@router.get("/sensor/schema")
async def get_sensor_schema():
    return {"sensors": [
        {"sensor_id": "dht22", "trend_metric": "temp_c", "fields": [
            {"field": "temp_c", "label": "Temp", "unit": "°C", "data_type": "float", "required": True},
            {"field": "hum", "label": "Humidity", "unit": "%", "data_type": "float", "required": True},
        ]},
        {"sensor_id": "soil_modbus_02", "trend_metric": "vwc", "fields": [
            {"field": "vwc", "label": "Soil VWC", "unit": "%", "data_type": "float", "required": True},
        ]}
    ]}

@router.get("/telemetry")
async def get_telemetry(device_id: str = None, limit: int = 30):
    now = datetime.utcnow()
    rows = []
    for i in range(limit):
        ts = now - timedelta(minutes=i*10)
        rows.append({
            "ts": ts.isoformat() + "Z",
            "device_id": device_id or "NODE-01-RICE",
            "sensor_id": "dht22",
            "fields": {"temp_c": round(26 + random.uniform(-2, 2), 1), "hum": round(65 + random.uniform(-5, 5), 1)}
        })
    return rows

@router.post("/chat")
async def chat_proxy(request: Request):
    data = await request.json()
    msg = data.get("message", "").lower()
    return {"reply": f"Hello! (AIT103 Rice Agent). I received: '{msg}'"}

@router.get("/health")
@router.get("/rice/health")
def health() -> dict:
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z", "model_loaded": _classifier is not None}

@router.post("/rice/predict", include_in_schema=False)
async def predict_rice(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    result = _predict(image_bytes)
    return result.model_dump()
