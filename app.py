# from fastapi import FastAPI, File, UploadFile
# from sqlalchemy.orm import Session
# from database import engine, SessionLocal
# from models import Base, Detection
# from datetime import datetime
# import json
# import requests
# import os

# app = FastAPI(title="Parental Control Backend")

# # Create DB tables
# Base.metadata.create_all(bind=engine)

# HF_TOKEN = os.getenv("HF_TOKEN")

# HF_API_URL = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"

# SEXUAL_THRESHOLD = 0.6


# # ================= HUGGINGFACE CALL =================

# def analyze_with_hf(image_bytes: bytes):

#     try:
#         response = requests.post(
#             HF_API_URL,
#             headers={
#                 "Authorization": f"Bearer {HF_TOKEN}",
#                 "Content-Type": "application/octet-stream"
#             },
#             data=image_bytes,
#             timeout=60
#         )
#     except requests.exceptions.RequestException as e:
#         return {"error": f"Network error: {str(e)}"}

#     # Debug print (check Render logs)
#     print("HF STATUS:", response.status_code)
#     print("HF RAW RESPONSE:", response.text[:300])

#     try:
#         data = response.json()
#     except Exception:
#         return {
#             "error": "Invalid JSON response",
#             "raw": response.text[:300]
#         }

#     if isinstance(data, dict) and "error" in data:
#         return {"error": data["error"]}

#     return data


# # ================= ANALYZE FRAME =================

# @app.post("/analyze-frame")
# async def analyze_frame(file: UploadFile = File(...)):

#     contents = await file.read()

#     hf_result = analyze_with_hf(contents)

#     # If HF returned error
#     if isinstance(hf_result, dict) and "error" in hf_result:
#         return {
#             "categories": [],
#             "sexual_score": 0.0,
#             "hf_error": hf_result["error"],
#             "timestamp": datetime.utcnow().isoformat()
#         }

#     sexual_score = 0.0

#     if isinstance(hf_result, list):
#         for item in hf_result:
#             if item["label"].lower() == "nsfw":
#                 sexual_score = item["score"]

#     categories = []
#     if sexual_score >= SEXUAL_THRESHOLD:
#         categories.append("sexual")

#     now = datetime.utcnow().isoformat()

#     if categories:
#         db: Session = SessionLocal()
#         detection = Detection(
#             timestamp=now,
#             sexual_score=sexual_score,
#             violent_score=0.0,
#             categories=json.dumps(categories)
#         )
#         db.add(detection)
#         db.commit()
#         db.close()

#     return {
#         "categories": categories,
#         "sexual_score": round(sexual_score, 3),
#         "timestamp": now
#     }


# # ================= SUMMARY =================

# @app.get("/parent-summary")
# def parent_summary():
#     db: Session = SessionLocal()
#     total = db.query(Detection).count()
#     db.close()
#     return {"total_bad_frames": total}


# @app.get("/")
# def health():
#     return {"status": "Backend Running"}


#----------SECOND-----------#

# from fastapi import FastAPI, File, UploadFile, Form
# from sqlalchemy.orm import Session
# from database import engine, SessionLocal
# from models import Base, Detection
# from datetime import datetime, timedelta
# import json
# import requests
# import os

# app = FastAPI(title="Parental Control Backend")

# Base.metadata.create_all(bind=engine)

# HF_TOKEN = os.getenv("HF_TOKEN")

# HF_API_URL = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"

# SEXUAL_THRESHOLD = 0.6


# # ===========================
# # HUGGINGFACE ANALYSIS
# # ===========================

# def analyze_with_hf(image_bytes: bytes):
#     try:
#         response = requests.post(
#             HF_API_URL,
#             headers={
#                 "Authorization": f"Bearer {HF_TOKEN}",
#                 "Content-Type": "application/octet-stream"
#             },
#             data=image_bytes,
#             timeout=60
#         )
#         return response.json()
#     except Exception as e:
#         print("HF ERROR:", str(e))
#         return []


# # ===========================
# # ANALYZE FRAME
# # ===========================

# @app.post("/analyze-frame")
# async def analyze_frame(
#     device_id: str = Form(...),
#     file: UploadFile = File(...)
# ):

#     contents = await file.read()

#     hf_result = analyze_with_hf(contents)

#     sexual_score = 0.0

#     if isinstance(hf_result, list):
#         for item in hf_result:
#             if item["label"].lower() == "nsfw":
#                 sexual_score = item["score"]

#     categories = []
#     if sexual_score >= SEXUAL_THRESHOLD:
#         categories.append("sexual")

#     now = datetime.utcnow()

#     if categories:
#         db: Session = SessionLocal()

#         detection = Detection(
#             device_id=device_id,
#             timestamp=now.isoformat(),
#             sexual_score=sexual_score,
#             violent_score=0.0,
#             categories=json.dumps(categories)
#         )

#         db.add(detection)
#         db.commit()
#         db.close()

#     return {
#         "categories": categories,
#         "sexual_score": round(sexual_score, 3),
#         "timestamp": now.isoformat()
#     }


# # ===========================
# # PARENT SUMMARY
# # ===========================

# @app.get("/parent-summary")
# def parent_summary(device_id: str):

#     db: Session = SessionLocal()

#     total_bad_frames = db.query(Detection).filter(
#         Detection.device_id == device_id
#     ).count()

#     detections = db.query(Detection).filter(
#         Detection.device_id == device_id
#     ).all()

#     db.close()

#     total_bad_watch_time_seconds = len(detections) * 5  # assuming 5 sec capture

#     return {
#         "total_bad_frames": total_bad_frames,
#         "estimated_watch_time_seconds": total_bad_watch_time_seconds
#     }


# # ===========================
# # ACTIVE INCIDENT
# # ===========================

# @app.get("/active-incident")
# def active_incident(device_id: str):

#     db: Session = SessionLocal()

#     last_detection = db.query(Detection).filter(
#         Detection.device_id == device_id
#     ).order_by(Detection.id.desc()).first()

#     db.close()

#     if not last_detection:
#         return {"active": False}

#     last_time = datetime.fromisoformat(last_detection.timestamp)

#     if datetime.utcnow() - last_time < timedelta(seconds=20):
#         return {
#             "active": True,
#             "last_detected_at": last_detection.timestamp
#         }

#     return {"active": False}


# @app.get("/")
# def health():
#     return {"status": "Backend Running"}


#----------THIRD---------#
# from fastapi import FastAPI, File, UploadFile, Form
# from sqlalchemy.orm import Session
# from database import engine, SessionLocal
# from models import Base, Detection
# from datetime import datetime, timedelta
# import json
# import requests
# import os

# app = FastAPI(title="Parental Control Backend")

# Base.metadata.create_all(bind=engine)

# HF_TOKEN = os.getenv("HF_TOKEN")

# HF_API_URL = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"

# SEXUAL_THRESHOLD = 0.2


# # =====================================
# # HUGGINGFACE ANALYSIS
# # =====================================

# def analyze_with_hf(image_bytes: bytes):
#     try:
#         response = requests.post(
#             HF_API_URL,
#             headers={
#                 "Authorization": f"Bearer {HF_TOKEN}",
#                 "Content-Type": "application/octet-stream"
#             },
#             data=image_bytes,
#             timeout=60
#         )
#         return response.json()
#     except Exception as e:
#         print("HF ERROR:", str(e))
#         return []


# # =====================================
# # ANALYZE FRAME
# # =====================================

# @app.post("/analyze-frame")
# async def analyze_frame(
#     device_id: str = Form(...),
#     file: UploadFile = File(...)
# ):

#     contents = await file.read()
#     hf_result = analyze_with_hf(contents)

#     sexual_score = 0.0

#     if isinstance(hf_result, list):
#         for item in hf_result:
#             if item["label"].lower() == "nsfw":
#                 sexual_score = item["score"]

#     categories = []
#     if sexual_score >= SEXUAL_THRESHOLD:
#         categories.append("sexual")

#     now = datetime.utcnow()

#     if categories:
#         db: Session = SessionLocal()

#         detection = Detection(
#             device_id=device_id,
#             timestamp=now.isoformat(),
#             sexual_score=sexual_score,
#             violent_score=0.0,
#             categories=json.dumps(categories)
#         )

#         db.add(detection)
#         db.commit()
#         db.close()

#     return {
#         "categories": categories,
#         "sexual_score": round(sexual_score, 3),
#         "timestamp": now.isoformat()
#     }


# # =====================================
# # SMART ACTIVE INCIDENT (UPGRADED)
# # =====================================

# @app.get("/active/{device_id}")
# def active_status(device_id: str):

#     db: Session = SessionLocal()

#     detections = (
#         db.query(Detection)
#         .filter(Detection.device_id == device_id)
#         .order_by(Detection.timestamp.desc())
#         .limit(5)
#         .all()
#     )

#     db.close()

#     if len(detections) < 2:
#         return {"active": False}

#     now = datetime.utcnow()
#     recent_count = 0

#     for d in detections:
#         ts = datetime.fromisoformat(d.timestamp)
#         if (now - ts).total_seconds() <= 15 and d.sexual_score >= 0.3:
#             recent_count += 1

#     active = recent_count >= 2

#     return {
#         "active": active,
#         "recent_detections": recent_count
#     }


# # =====================================
# # RISK SCORING ENGINE
# # =====================================

# @app.get("/risk/{device_id}")
# def risk_score(device_id: str):

#     db: Session = SessionLocal()

#     detections = (
#         db.query(Detection)
#         .filter(Detection.device_id == device_id)
#         .order_by(Detection.timestamp.desc())
#         .limit(10)
#         .all()
#     )

#     db.close()

#     if not detections:
#         return {"risk_score": 0, "risk_level": "LOW"}

#     scores = [d.sexual_score for d in detections]
#     avg_score = sum(scores) / len(scores)

#     if avg_score > 0.35:
#         level = "HIGH"
#     elif avg_score > 0.2:
#         level = "MEDIUM"
#     else:
#         level = "LOW"

#     return {
#         "risk_score": round(avg_score * 100, 2),
#         "risk_level": level
#     }


# # =====================================
# # SUMMARY
# # =====================================

# @app.get("/summary/{device_id}")
# def parent_summary(device_id: str):

#     db: Session = SessionLocal()

#     detections = db.query(Detection).filter(
#         Detection.device_id == device_id
#     ).all()

#     db.close()

#     total_bad_frames = len(detections)
#     estimated_watch_time_seconds = total_bad_frames * 5

#     return {
#         "total_bad_frames": total_bad_frames,
#         "estimated_watch_time_seconds": estimated_watch_time_seconds
#     }


# @app.get("/")
# def health():
#     return {"status": "Backend Running"}


#-------FOURTH------------#
from fastapi import FastAPI, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Detection
from datetime import datetime, timedelta
import json
import requests
import os
from models import Detection, Incident
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

app = FastAPI(title="Parental Control Backend")

Base.metadata.create_all(bind=engine)

HF_TOKEN = os.getenv("HF_TOKEN")

HF_API_URL = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"

SEXUAL_THRESHOLD = 0.03


# =====================================
# HUGGINGFACE ANALYSIS
# =====================================

def analyze_with_hf(image_bytes: bytes):
    try:
        response = requests.post(
            HF_API_URL,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/octet-stream"
            },
            data=image_bytes,
            timeout=60
        )
        return response.json()
    except Exception as e:
        print("HF ERROR:", str(e))
        return []


# =====================================
# ANALYZE FRAME
# =====================================

@app.post("/analyze-frame")
async def analyze_frame(
    device_id: str = Form(...),
    file: UploadFile = File(...)
):

    contents = await file.read()
    hf_result = analyze_with_hf(contents)

    sexual_score = 0.0

    if isinstance(hf_result, list):
        for item in hf_result:
            if item["label"].lower() == "nsfw":
                sexual_score = item["score"]

    categories = []
    if sexual_score >= 0.5:
        categories.append("high")
    elif sexual_score >= 0.15:
        categories.append("medium")
    elif sexual_score >= 0.03:
        categories.append("low")

    now = datetime.utcnow()
    print("Sexual score:", sexual_score)
    print("Categories:", categories)
    if sexual_score >= 0.03:
        db: Session = SessionLocal()

        detection = Detection(
            device_id=device_id,
            timestamp=now.isoformat(),
            sexual_score=sexual_score,
            violent_score=0.0,
            categories=json.dumps(categories)
        )

        db.add(detection)
        db.commit()
        db.close()

    return {
        "categories": categories,
        "sexual_score": round(sexual_score, 3),
        "timestamp": now.isoformat()
    }


# =====================================
# ACTIVE INCIDENT (WINDOW BASED)
# =====================================

@app.get("/active/{device_id}")
def active_status(device_id: str):

    db: Session = SessionLocal()

    now = datetime.utcnow()
    window_start = now - timedelta(seconds=20)

    recent_detections = (
        db.query(Detection)
        .filter(
            Detection.device_id == device_id,
            Detection.timestamp >= window_start.isoformat()
        )
        .all()
    )

    db.close()

    active = len(recent_detections) >= 2

    return {
        "active": active,
        "recent_detections": len(recent_detections)
    }


# =====================================
# PROFESSIONAL INCIDENT RISK ENGINE
# =====================================
@app.get("/risk/{device_id}")
def risk_score(device_id: str):

    db: Session = SessionLocal()

    now = datetime.utcnow()
    window_start = now - timedelta(seconds=30)

    recent_detections = (
        db.query(Detection)
        .filter(
            Detection.device_id == device_id,
            Detection.timestamp >= window_start.isoformat()
        )
        .all()
    )

    # -------- CALCULATE RISK -------- #

    if not recent_detections:
        # If no recent detections, close active incident if exists
        active_incident = (
            db.query(Incident)
            .filter(
                Incident.device_id == device_id,
                Incident.status == "ACTIVE"
            )
            .first()
        )

        if active_incident:
            active_incident.status = "CLOSED"
            active_incident.ended_at = now.isoformat()
            db.commit()

        db.close()

        return {
            "risk_score": 0,
            "risk_level": "SAFE",
            "incident_active": False
        }

    detection_count = len(recent_detections)
    avg_score = sum(d.sexual_score for d in recent_detections) / detection_count

    timestamps = [datetime.fromisoformat(d.timestamp) for d in recent_detections]
    session_duration = (max(timestamps) - min(timestamps)).total_seconds()

    risk_score = (
        detection_count * 10 +
        avg_score * 50 +
        session_duration * 0.5
    )

    # -------- CLASSIFY -------- #

    if risk_score > 80:
        level = "CRITICAL"
    elif risk_score > 50:
        level = "HIGH"
    elif risk_score > 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    # -------- INCIDENT MANAGEMENT -------- #

    active_incident = (
        db.query(Incident)
        .filter(
            Incident.device_id == device_id,
            Incident.status == "ACTIVE"
        )
        .first()
    )

    if not active_incident and level in ["MEDIUM", "HIGH", "CRITICAL"]:
        # Start new incident
        new_incident = Incident(
            device_id=device_id,
            started_at=now.isoformat(),
            peak_risk=risk_score,
            status="ACTIVE"
        )
        db.add(new_incident)
        db.commit()

    elif active_incident:
        # Update peak risk if higher
        if risk_score > active_incident.peak_risk:
            active_incident.peak_risk = risk_score
            db.commit()

    db.close()

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": level,
        "incident_active": True,
        "detections_last_30s": detection_count,
        "session_duration_seconds": int(session_duration)
    }
# =====================================
# SUMMARY
# =====================================

@app.get("/summary/{device_id}")
def parent_summary(device_id: str):

    db: Session = SessionLocal()

    detections = db.query(Detection).filter(
        Detection.device_id == device_id
    ).all()

    db.close()

    total_bad_frames = len(detections)
    estimated_watch_time_seconds = total_bad_frames * 5

    return {
        "total_bad_frames": total_bad_frames,
        "estimated_watch_time_seconds": estimated_watch_time_seconds
    }


@app.get("/")
def health():
    return {"status": "Backend Running"}

from fastapi import Body

@app.post("/app-event")
def app_event(data: dict = Body(...)):

    device_id = data.get("device_id")
    package_name = data.get("package_name")

    print("App Opened:", package_name)

    return {"status": "received"}

#-------INCIDENTS-------#
@app.get("/incidents/{device_id}")
def get_incidents(device_id: str):

    db: Session = SessionLocal()

    incidents = (
        db.query(Incident)
        .filter(Incident.device_id == device_id)
        .order_by(Incident.started_at.desc())
        .all()
    )

    now = datetime.utcnow()

    result = []

    for inc in incidents:

        if inc.ended_at:
            duration = (
                datetime.fromisoformat(inc.ended_at) -
                datetime.fromisoformat(inc.started_at)
            ).total_seconds()
        else:
            duration = (
                now -
                datetime.fromisoformat(inc.started_at)
            ).total_seconds()

        result.append({
            "started_at": inc.started_at,
            "ended_at": inc.ended_at,
            "peak_risk": round(inc.peak_risk, 2),
            "status": inc.status,
            "duration_seconds": int(duration)
        })

    db.close()

    return {
        "incident_count": len(result),
        "incidents": result
    }