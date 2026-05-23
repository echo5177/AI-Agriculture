"""Smart Farm AI Engine (AIT103 Academic Prototype)
Entry point for the FastAPI application.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse

# Consolidated import: all inference/storage logic is here
from ai_engine.crops.rice.inference.api import router, set_classifier, set_yolo_detector, ImageLoadError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Config
MODEL_CHECKPOINT_PATH = os.environ.get("MODEL_CHECKPOINT_PATH", "models/rice/rice_leaf_classifier/best_model.pth")
MODEL_LABELS_FILE = os.environ.get("MODEL_LABELS_FILE", "models/rice/rice_leaf_classifier/labels.json")
MODEL_CONFIG_FILE = os.environ.get("MODEL_CONFIG_FILE", "models/rice/rice_leaf_classifier/config.yaml")
MODEL_ADVICE_FILE = os.environ.get("MODEL_ADVICE_FILE", "models/rice/rice_leaf_classifier/advice_map.yaml")
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "models/yolov8_rice_leaf.pt")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Smart Farm AI Engine Starting (AIT103 Prototype) ===")

    # --- Priority 1: YOLO Object Detector ---
    try:
        if os.path.exists(YOLO_MODEL_PATH):
            from ai_engine.crops.rice.inference.yolo_detector import YoloDetector
            logger.info("Loading YOLO model from: %s", YOLO_MODEL_PATH)
            detector = YoloDetector(model_path=YOLO_MODEL_PATH)
            set_yolo_detector(detector)
            logger.info("YOLO detector loaded successfully (%d classes).", len(detector.class_names))
        else:
            logger.warning("YOLO weights not found at %s – skipping.", YOLO_MODEL_PATH)
    except Exception as exc:
        logger.error("YOLO detector failed to load: %s", exc)

    # --- Priority 2: Legacy Classifier (fallback) ---
    try:
        from ai_engine.crops.rice.inference.rice_leaf_classifier import RiceLeafClassifier
        logger.info("Loading legacy Rice Classifier...")
        classifier = RiceLeafClassifier(
            checkpoint_path=MODEL_CHECKPOINT_PATH,
            labels_file=MODEL_LABELS_FILE,
            config_file=MODEL_CONFIG_FILE,
            advice_file=MODEL_ADVICE_FILE,
        )
        set_classifier(classifier)
        logger.info("Legacy classifier loaded (fallback ready).")
    except Exception as exc:
        logger.error("Legacy classifier failed to load: %s", exc)

    yield
    logger.info("=== Smart Farm AI Engine Shutting Down ===")

app = FastAPI(
    title="Smart Farm AI Engine (AIT103)",
    lifespan=lifespan,
)

# CORS: Simplified for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Single router handles inference, storage, and mock telemetry
app.include_router(router, prefix="/api/v1")

# Static Files & Dashboard
app.mount("/static", StaticFiles(directory="frontend/rice"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/rice_dashboard.html")

app.mount("/", StaticFiles(directory="frontend/rice", html=True), name="frontend")

# Exception Handlers
@app.exception_handler(ImageLoadError)
async def image_load_error_handler(request: Request, exc: ImageLoadError):
    return JSONResponse(status_code=422, content={"status": "error", "message": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"status": "error", "message": "Internal error"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )
