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
from models import Detection, Incident, ParentDevice, DeviceCommand, AppUsage, ScreenLimit,BlockedApp,InstalledApp
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, messaging
from fastapi import Body




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

    # -------------------------------
    # NO RECENT DETECTIONS
    # -------------------------------

    if not recent_detections:

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

    # -------------------------------
    # CALCULATE RISK
    # -------------------------------

    detection_count = len(recent_detections)
    avg_score = sum(d.sexual_score for d in recent_detections) / detection_count

    timestamps = [datetime.fromisoformat(d.timestamp) for d in recent_detections]
    session_duration = (max(timestamps) - min(timestamps)).total_seconds()

    risk_score = (
        detection_count * 10 +
        avg_score * 50 +
        session_duration * 0.5
    )

    # -------------------------------
    # CLASSIFY LEVEL
    # -------------------------------

    if risk_score > 80:
        level = "CRITICAL"
    elif risk_score > 50:
        level = "HIGH"
    elif risk_score > 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    # -------------------------------
    # INCIDENT MANAGEMENT
    # -------------------------------

    active_incident = (
        db.query(Incident)
        .filter(
            Incident.device_id == device_id,
            Incident.status == "ACTIVE"
        )
        .first()
    )

    # 🚨 NEW INCIDENT TRIGGER
    if not active_incident and level in ["MEDIUM", "HIGH", "CRITICAL"]:

        print("🔥 Starting new incident")

        new_incident = Incident(
            device_id=device_id,
            started_at=now.isoformat(),
            peak_risk=risk_score,
            status="ACTIVE"
        )

        db.add(new_incident)
        db.commit()

        # -------------------------------
        # FETCH PARENT TOKEN
        # -------------------------------

        parent = (
            db.query(ParentDevice)
            .filter(ParentDevice.device_id == "parent_device_2")
            .first()
        )

        if parent:
            print("📲 Sending push to parent")

            send_push(
                parent.fcm_token,
                "⚠️ ALERT",
                f"Risk Level: {level}"
            )
        else:
            print("❌ No parent device found")

    # UPDATE EXISTING INCIDENT
    elif active_incident:
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
    
## parent api 
from sqlalchemy.orm import Session
from models import ParentDevice
@app.post("/register-parent")
def register_parent(device_id: str, fcm_token: str):

    db: Session = SessionLocal()

    existing = db.query(ParentDevice).filter(
        ParentDevice.device_id == device_id
    ).first()

    if existing:
        existing.fcm_token = fcm_token
    else:
        parent = ParentDevice(
            device_id=device_id,
            fcm_token=fcm_token
        )
        db.add(parent)

    db.commit()
    db.close()

    return {"status": "registered"}


def send_push(token: str, title: str, body: str):
    try:
        message = messaging.Message(
    data={
        "title": title,
        "body": body,
    },
    token=token,
)

        response = messaging.send(message)
        print("Push sent:", response)

    except Exception as e:
        print("Push failed:", str(e))

@app.post("/test-push/{device_id}")
def test_push(device_id: str):

    db = SessionLocal()

    parent = db.query(ParentDevice).filter(
        ParentDevice.device_id == device_id
    ).first()

    if not parent:
        db.close()
        return {"error": "Parent device not found"}

    send_push(
        parent.fcm_token,
        "Test Alert",
        "Push system working"
    )

    db.close()

    return {"status": "push sent"}


from models import DeviceCommand
from datetime import datetime
from fastapi import Body

@app.post("/commands/send")
def send_command(data: dict = Body(...)):

    device_id = data.get("device_id")
    command_type = data.get("command_type")
    payload = data.get("payload", "")

    db = SessionLocal()

    command = DeviceCommand(
        device_id=device_id,
        command_type=command_type,
        payload=payload,
        status="PENDING",
        created_at=datetime.utcnow().isoformat()
    )

    db.add(command)
    db.commit()
    db.close()

    return {"status": "command_sent"}

@app.get("/commands/pending/{device_id}")
def get_pending_command(device_id: str):

    db = SessionLocal()

    command = (
        db.query(DeviceCommand)
        .filter(
            DeviceCommand.device_id == device_id,
            DeviceCommand.status == "PENDING"
        )
        .order_by(DeviceCommand.created_at.asc())
        .first()
    )

    if not command:
        db.close()
        return {"command": None}

    result = {
        "id": command.id,
        "command_type": command.command_type,
        "payload": command.payload
    }

    db.close()

    return {"command": result}

@app.post("/commands/executed")
def command_executed(data: dict = Body(...)):

    command_id = data.get("command_id")

    db = SessionLocal()

    command = db.query(DeviceCommand).filter(
        DeviceCommand.id == command_id
    ).first()

    if not command:
        db.close()
        return {"error": "command not found"}

    command.status = "EXECUTED"
    command.executed_at = datetime.utcnow().isoformat()

    db.commit()
    db.close()

    return {"status": "updated"}

from models import AppUsage

@app.post("/app-usage")
def store_app_usage(data: dict = Body(...)):

    device_id = data.get("device_id")
    package_name = data.get("package_name")
    started_at = data.get("started_at")
    ended_at = data.get("ended_at")
    duration_seconds = data.get("duration_seconds")

    db = SessionLocal()

    usage = AppUsage(
        device_id=device_id,
        package_name=package_name,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds
    )

    db.add(usage)
    db.commit()
    db.close()

    return {"status": "usage_saved"}

@app.get("/dashboard/overview/{device_id}")
def dashboard_overview(device_id: str):

    db = SessionLocal()

    today = datetime.utcnow().date().isoformat()

    usages = db.query(AppUsage).filter(
        AppUsage.device_id == device_id,
        AppUsage.started_at.startswith(today)
    ).all()

    total_screen_time = sum(u.duration_seconds for u in usages)

    incidents_today = db.query(Incident).filter(
        Incident.device_id == device_id,
        Incident.started_at.startswith(today)
    ).count()

    db.close()

    return {
        "total_screen_time_seconds": total_screen_time,
        "incidents_today": incidents_today
    }
    
@app.get("/commands/history/{device_id}")
def command_history(device_id: str):

    db = SessionLocal()

    commands = (
        db.query(DeviceCommand)
        .filter(DeviceCommand.device_id == device_id)
        .order_by(DeviceCommand.created_at.desc())
        .all()
    )

    result = []

    for cmd in commands:
        result.append({
            "id": cmd.id,
            "command_type": cmd.command_type,
            "status": cmd.status,
            "created_at": cmd.created_at,
            "executed_at": cmd.executed_at
        })

    db.close()

    return {"commands": result}

@app.get("/usage/{device_id}")
def get_usage(device_id: str):

    db = SessionLocal()

    usage = db.query(AppUsage).filter(
        AppUsage.device_id == device_id
    ).all()

    db.close()

    total_time = sum(u.duration_seconds for u in usage)

    return {
        "total_screen_time": total_time,
        "apps": [
            {
                "package": u.package_name,
                "duration": u.duration_seconds
            }
            for u in usage
        ]
    }
    
@app.get("/top-apps/{device_id}")
def top_apps(device_id: str):

    db = SessionLocal()

    usage = db.query(AppUsage).filter(
        AppUsage.device_id == device_id
    ).all()

    db.close()

    app_time = {}

    for u in usage:
        app_time[u.package_name] = app_time.get(u.package_name, 0) + u.duration_seconds

    sorted_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)

    return {
        "top_apps": [
            {"package": a, "duration": d}
            for a, d in sorted_apps[:5]
        ]
    }
@app.post("/set-limit")
def set_limit(data: dict = Body(...)):

    device_id = data.get("device_id")
    limit = data.get("limit")

    db: Session = SessionLocal()

    existing = db.query(ScreenLimit).filter(
        ScreenLimit.device_id == device_id
    ).first()

    if existing:
        existing.daily_limit_minutes = limit
    else:
        db.add(ScreenLimit(
            device_id=device_id,
            daily_limit_minutes=limit
        ))

    db.commit()
    db.close()

    return {"status": "limit set"}

@app.get("/limit/{device_id}")
def get_limit(device_id: str):

    db: Session = SessionLocal()

    limit = db.query(ScreenLimit).filter(
        ScreenLimit.device_id == device_id
    ).first()

    db.close()

    if not limit:
        return {"limit": None}

    return {"limit": limit.daily_limit_minutes}

@app.post("/block-app")
def block_app(data: dict = Body(...)):

    device_id = data.get("device_id")
    package_name = data.get("package_name")

    db = SessionLocal()

    existing = db.query(BlockedApp).filter(
        BlockedApp.device_id == device_id,
        BlockedApp.package_name == package_name
    ).first()

    if not existing:
        db.add(BlockedApp(
            device_id=device_id,
            package_name=package_name
        ))

    db.commit()
    db.close()

    return {"status": "blocked"}

@app.get("/blocked-apps/{device_id}")
def get_blocked_apps(device_id: str):

    db = SessionLocal()

    apps = db.query(BlockedApp).filter(
        BlockedApp.device_id == device_id
    ).all()

    db.close()

    return {
        "blocked_apps": [a.package_name for a in apps]
    }
    
@app.post("/installed-apps")
def save_installed_apps(data: dict = Body(...)):

    device_id = data.get("device_id")
    apps = data.get("apps")

    db: Session = SessionLocal()

    for package in apps:

        existing = db.query(InstalledApp).filter(
            InstalledApp.device_id == device_id,
            InstalledApp.package_name == package
        ).first()

        if not existing:

            db.add(
                InstalledApp(
                    device_id=device_id,
                    package_name=package
                )
            )

    db.commit()
    db.close()

    return {"status": "saved"}

@app.get("/apps/{device_id}")
def get_apps(device_id:str):

    db = SessionLocal()

    apps = db.query(InstalledApp).filter(
        InstalledApp.device_id == device_id
    ).all()

    blocked = db.query(BlockedApp).filter(
        BlockedApp.device_id == device_id
    ).all()

    blocked_set = {b.package_name for b in blocked}

    db.close()

    return {
        "apps":[
            {
                "name":a.app_name,
                "package":a.package_name,
                "blocked":a.package_name in blocked_set
            }
            for a in apps
        ]
    }
    
@app.post("/unblock-app")
def unblock_app(data: dict = Body(...)):

    device_id = data.get("device_id")
    package_name = data.get("package_name")

    db = SessionLocal()

    db.query(BlockedApp).filter(
        BlockedApp.device_id == device_id,
        BlockedApp.package_name == package_name
    ).delete()

    db.commit()
    db.close()

    return {"status":"unblocked"}