from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
from fastapi.responses import StreamingResponse
import threading
import numpy as np
import base64
import cv2
import os
import csv

from ai_model import AIModule
from database import (
    init_db,
    save_detection,
    get_all_detections,
    get_detections_by_date
)

# ----------------------------
# PLC Simulation State
# ----------------------------
conveyor_running = True
emergency_triggered = False

# ----------------------------
# Initialize App
# ----------------------------
app = FastAPI(title="iMGS AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Setup
# ----------------------------
UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()
ai = AIModule()

# ----------------------------
# FOD Logic
# ----------------------------
def check_fod(detections):
    alerts = []
    for obj in detections:
        if obj["class"].lower() != "coal":
            alerts.append("Foreign Object Detected")
    return alerts


# ----------------------------
# Home
# ----------------------------
@app.get("/")
def home():
    return {"message": "iMGS AI Backend Running Successfully 🚀"}


# ----------------------------
# Predict
# ----------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    global conveyor_running, emergency_triggered

    # ----------------------------
    # 1️⃣ Read & Decode Image
    # ----------------------------
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # ----------------------------
    # 2️⃣ Run AI Detection
    # ----------------------------
    detections = ai.predict(img)

    # ----------------------------
    # 3️⃣ Save Detections to Database
    # ----------------------------
    for obj in detections:
        label = obj.get("class", "unknown")
        conf = obj.get("confidence", 0)
        save_detection(label, conf)


    # ----------------------------
    # 4️⃣ Granulometry Calculation
    # ----------------------------
    fine_count = sum(1 for d in detections if d.get("size_category") == "Fine")
    medium_count = sum(1 for d in detections if d.get("size_category") == "Medium")
    oversize_count = sum(1 for d in detections if d.get("size_category") == "Oversize")

    total = len(detections)

    fine_pct = (fine_count / total) * 100 if total else 0
    medium_pct = (medium_count / total) * 100 if total else 0
    oversize_pct = (oversize_count / total) * 100 if total else 0
     
    # ----------------------------
    # PLC Logic
    # ----------------------------
    if oversize_pct > 40:
        emergency_triggered = True
        conveyor_running = False
    else:
        emergency_triggered = False

    emergency_stop = oversize_pct > 40

    # ----------------------------
    # 6️⃣ Quality Score Logic
    # ----------------------------
    quality_score = 100 - (oversize_pct * 0.8 + medium_pct * 0.4)
    quality_score = max(0, round(quality_score, 2))

    if quality_score >= 80:
        quality_status = "GOOD"
    elif quality_score >= 50:
        quality_status = "MODERATE"
    else:
        quality_status = "POOR"

    # ----------------------------
    # 7️⃣ Foreign Object Detection
    # ----------------------------
    alerts = []

    for obj in detections:
        if obj.get("class", "").lower() != "coal":
            alerts.append("Foreign Object Detected")

    if emergency_stop:
        alerts.append("EMERGENCY STOP REQUIRED")


    # ----------------------------
    # 8️⃣ Draw Bounding Boxes
    # ----------------------------
    for obj in detections:
        bbox = obj.get("bbox", [0, 0, 0, 0])

        # Ensure bbox format is correct
        if isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        elif isinstance(bbox, list) and len(bbox) > 0:
            x1, y1, x2, y2 = bbox[0]
        else:
            continue

        label = obj.get("class", "unknown")
        conf = obj.get("confidence", 0)
        size = obj.get("size_category", "Medium")

        if size == "Oversize":
            color = (0, 0, 255)
        elif size == "Medium":
            color = (0, 165, 255)
        else:
            color = (0, 255, 0)

        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

        cv2.putText(
            img,
            f"{label} | {size} | {conf}",
            (int(x1), int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # ----------------------------
    # 9️⃣ Convert Image to Base64
    # ----------------------------
    _, buffer = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    # ----------------------------
    # 🔟 Final Response
    # ----------------------------
    return {
        "timestamp": datetime.now().isoformat(),
        "total_detections": total,
        "objects": detections,
        "alerts": alerts,
        "granulometry": {
            "fine_percentage": round(fine_pct, 2),
            "medium_percentage": round(medium_pct, 2),
            "oversize_percentage": round(oversize_pct, 2)
        },
        "quality": {
            "score": quality_score,
            "status": quality_status,
            "emergency_stop": emergency_stop
        },
        "image": img_base64
    }

# ----------------------------
# Flow Analytics
# ----------------------------
@app.get("/flow")
def flow_rate():
    belt_speed = 2.1
    material_area = np.random.uniform(0.5, 1.5)
    volumetric_flow = material_area * belt_speed * 3600

    return {
        "belt_speed": belt_speed,
        "material_area": material_area,
        "volumetric_flow_m3_hr": volumetric_flow
    }


# ----------------------------
# Health
# ----------------------------
@app.get("/health")
def health():
    return {
        "server_status": "running",
        "database_status": "connected",
        "model_loaded": True,
        "timestamp": datetime.now().isoformat()
    }


# ----------------------------
# History
# ----------------------------

@app.get("/history")
def history():
    return {"history": get_all_detections()}


# ----------------------------
# Export CSV
# ----------------------------

@app.get("/export")
def export_csv():

    data = get_all_detections()
    file_path = "detections_report.csv"

    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Label", "Confidence", "Timestamp"])

        for item in data:
            writer.writerow([
                item["id"],
                item["label"],
                item["confidence"],
                item["timestamp"]
            ])

    return FileResponse(
        file_path,
        media_type="text/csv",
        filename="detections_report.csv"
    )
 
# Try to open webcam (may fail in Docker)
try:
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        camera = None
except:
    camera = None

def generate_frames():

    if camera is None:
        return

    while True:
        success, frame = camera.read()
        if not success:
            break

        detections = ai.predict(frame)

        # Draw bounding boxes
        for obj in detections:
            x1, y1, x2, y2 = obj["bbox"][0]
            label = obj["class"]

            color = (0, 255, 0)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            cv2.putText(
                frame,
                label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )
@app.get("/live")
def live_camera():
    return StreamingResponse(generate_frames(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/plc_status")
def plc_status():
    return {
        "conveyor_running": conveyor_running,
        "emergency_triggered": emergency_triggered
    }

@app.post("/reset_system")
def reset_system():
    global conveyor_running, emergency_triggered
    conveyor_running = True
    emergency_triggered = False
    return {"message": "System Reset Successful"}

@app.get("/analytics")
def analytics():

    data = get_all_detections()

    if not data:
        return {
            "total_records": 0,
            "average_confidence": 0,
            "oversize_count": 0
        }

    total = len(data)

    # Count oversize events (based on label logic)
    oversize_count = sum(1 for d in data if d["label"].lower() != "coal")

    avg_conf = sum(d["confidence"] for d in data) / total

    return {
        "total_records": total,
        "average_confidence": round(avg_conf, 2),
        "oversize_count": oversize_count
    }
    
