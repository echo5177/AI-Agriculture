from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
import shutil
from datetime import datetime

from ai_engine.common.adapters.image_adapter import validate_image_bytes
from ai_engine.common.schemas.prediction import PredictionResponse

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


@router.post("/predict", include_in_schema=False)
async def predict_legacy(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    result = _predict(image_bytes)
    return result.model_dump()


@router.post("/rice/predict")
async def predict_rice(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()
    result = _predict(image_bytes)
    return result.model_dump()


UPLOAD_DIR = "local_data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/image/upload")
async def upload_image(
    file: UploadFile = File(...),
    device_id: str = Query(...),
    ts: str = Query(None),
    location: str = Query(None),
    crop_type: str = Query(None),
    farm_note: str = Query(None)
):
    """Handle image upload, store locally, and run inference."""
    try:
        # 1. Generate unique ID and save file
        upload_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        file_path = os.path.join(UPLOAD_DIR, f"{upload_id}{ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Read back for inference
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        
        # 3. Run AI Inference
        prediction = _predict(image_bytes)
        
        # 4. Save metadata for persistence (to be read by mock_api)
        meta_path = os.path.join(UPLOAD_DIR, f"{upload_id}.json")
        import json
        with open(meta_path, "w", encoding="utf-8") as fmeta:
            json.dump({
                "predicted_class": prediction.predicted_class,
                "confidence": prediction.confidence,
                "disease_rate": prediction.metadata.get("disease_rate", 0.0),
                "captured_at": ts or datetime.utcnow().isoformat() + "Z"
            }, fmeta)

        # 5. Return combined result matching frontend expectations
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
    """Serve the actual image file to the frontend."""
    if upload_id:
        # Search for the file with any extension in the upload dir
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(upload_id):
                return FileResponse(os.path.join(UPLOAD_DIR, f))
    
    if saved_path:
        if os.path.exists(saved_path):
            return FileResponse(saved_path)
            
    raise HTTPException(status_code=404, detail="Image not found")

@router.get("/rice/health")
def rice_health() -> dict:
    return {
        "status": "ok",
        "profile": "rice",
        "model_loaded": _classifier is not None,
    }
