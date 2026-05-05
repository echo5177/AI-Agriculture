from fastapi import APIRouter, Request, Query
from datetime import datetime, timedelta
import random
import uuid
import os

router = APIRouter(tags=["mock"])

# Mock Devices
DEVICES = [
    {"device_id": "NODE-01-RICE", "location": "North Terrace", "crop_type": "Rice", "farm_note": "AIT103 Sample Field", "sensors": ["dht22", "soil_modbus_02"], "registered_at_epoch_sec": 1714800000},
    {"device_id": "NODE-02-RICE", "location": "South Terrace", "crop_type": "Rice", "farm_note": "AIT103 Control Plot", "sensors": ["dht22"], "registered_at_epoch_sec": 1714810000},
    {"device_id": "MOBILE-GW", "location": "Field Office", "crop_type": "Rice", "farm_note": "Mobile Gateway", "sensors": ["system"], "registered_at_epoch_sec": 1714820000},
]

@router.get("/devices")
async def get_devices():
    return {"devices": DEVICES}

@router.get("/sensor/schema")
async def get_sensor_schema():
    return {
        "sensors": [
            {
                "sensor_id": "dht22",
                "trend_metric": "temp_c",
                "fields": [
                    {"field": "temp_c", "label": "Temp", "unit": "°C", "data_type": "float", "required": True, "threshold_low": 15, "threshold_high": 40},
                    {"field": "hum", "label": "Humidity", "unit": "%", "data_type": "float", "required": True, "threshold_low": 20, "threshold_high": 95},
                ]
            },
            {
                "sensor_id": "soil_modbus_02",
                "trend_metric": "vwc",
                "fields": [
                    {"field": "vwc", "label": "Soil VWC", "unit": "%", "data_type": "float", "required": True, "threshold_low": 10, "threshold_high": 80},
                    {"field": "temp_c", "label": "Soil Temp", "unit": "°C", "data_type": "float", "required": True},
                ]
            }
        ]
    }

@router.get("/telemetry")
async def get_telemetry(
    device_id: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 50
):
    rows = []
    now = datetime.utcnow()
    if not start_time:
        start_dt = now - timedelta(hours=24)
    else:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if not end_time:
        end_dt = now
    else:
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    target_device = next((d for d in DEVICES if d["device_id"] == device_id), DEVICES[0])
    sensors = target_device["sensors"]

    for i in range(min(limit, 30)):
        ts = start_dt + (end_dt - start_dt) * (i / 30)
        for s_id in sensors:
            fields = {}
            if s_id == "dht22":
                fields = {"temp_c": round(26 + random.uniform(-4, 4), 1), "hum": round(65 + random.uniform(-10, 10), 1)}
            elif s_id == "soil_modbus_02":
                fields = {"vwc": round(35 + random.uniform(-5, 5), 1), "temp_c": round(23 + random.uniform(-2, 2), 1)}
            
            rows.append({
                "ts": ts.isoformat() + "Z",
                "device_id": target_device["device_id"],
                "sensor_id": s_id,
                "fields": fields
            })
    return rows

@router.get("/image/uploads")
async def get_image_uploads(limit: int = 10):
    uploads = []
    
    # 1. Add real uploads from local_data/uploads if any
    upload_dir = "local_data/uploads"
    if os.path.exists(upload_dir):
        import json
        files = [f for f in os.listdir(upload_dir) if not f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), reverse=True)
        for f in files[:limit]:
            uid = os.path.splitext(f)[0]
            mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(upload_dir, f)))
            
            # Try to load real metadata
            meta_path = os.path.join(upload_dir, f"{uid}.json")
            real_meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as fm:
                        real_meta = json.load(fm)
                except:
                    pass

            uploads.append({
                "upload_id": uid,
                "device_id": "MOBILE-CAM",
                "captured_at": real_meta.get("captured_at") or mtime.isoformat() + "Z",
                "upload_status": "inferred",
                "predicted_class": real_meta.get("predicted_class") or "Processing...",
                "disease_rate": real_meta.get("disease_rate") or 0.0
            })

    # 2. Add some mock data if we have few real files
    if len(uploads) < limit:
        classes = ["HealthyLeaf", "BrownSpot", "LeafBlast", "BacterialLeafBlight"]
        for i in range(limit - len(uploads)):
            uploads.append({
                "upload_id": str(uuid.uuid4()),
                "device_id": "MOCK-DEV",
                "captured_at": (datetime.utcnow() - timedelta(minutes=(i+1)*45)).isoformat() + "Z",
                "upload_status": "inferred",
                "predicted_class": random.choice(classes),
                "disease_rate": round(random.uniform(0.1, 0.45), 3)
            })
            
    return uploads[:limit]

@router.post("/chat")
async def chat_proxy(request: Request):
    data = await request.json()
    msg = data.get("message", "").lower()
    return {"reply": f"Hello! (AIT103 Rice Agent). I received your message: '{msg}'"}
