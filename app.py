
#-------FOURTH------------#
from fastapi import FastAPI, File, UploadFile, Form, Body
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Detection, Incident, ParentDevice, DeviceCommand, AppUsage, ScreenLimit, BlockedApp, InstalledApp
from datetime import datetime, timedelta
import json
import requests
import os
import firebase_admin
from firebase_admin import credentials, messaging




app = FastAPI(title="Parental Control Backend")



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

    try:
        db: Session = SessionLocal()

        recent_detections = (
            db.query(Detection)
            .filter(Detection.device_id == device_id)
            .all()
        )

        active = len(recent_detections) >= 2

        return {
            "active": active,
            "recent_detections": len(recent_detections)
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()


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
    started_at = str(data.get("started_at"))
    ended_at = str(data.get("ended_at"))
    duration_seconds = data.get("duration_seconds")

    if not device_id or not package_name or not started_at or not ended_at or duration_seconds is None:
        return {"error": "missing fields"}

    db = SessionLocal()

    try:
        today = started_at[:10]

        existing = db.query(AppUsage).filter(
            AppUsage.device_id == device_id,
            AppUsage.package_name == package_name,
            AppUsage.started_at.startswith(today)
        ).first()

        if existing:
            existing.duration_seconds += int(duration_seconds)
            existing.ended_at = ended_at
        else:
            usage = AppUsage(
                device_id=device_id,
                package_name=package_name,
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=int(duration_seconds)
            )
            db.add(usage)

        db.commit()

    except Exception as e:
        db.rollback()
        print("APP USAGE ERROR:", e)

    finally:
        db.close()

    return {"status": "usage_saved"}

@app.get("/dashboard/overview/{device_id}")
def dashboard_overview(device_id: str):

    db = SessionLocal()

    rows = db.query(AppUsage).filter(
        AppUsage.device_id == device_id
    ).all()

    today = datetime.utcnow().date()

    total_seconds = 0

    for r in rows:

        try:
            ts = datetime.utcfromtimestamp(int(r.started_at) / 1000)
        except:
            continue

        if ts.date() != today:
            continue

        if r.package_name in [
            "com.android.systemui",
            "com.google.android.apps.nexuslauncher",
            "com.example.childcontrol"
        ]:
            continue

        total_seconds += r.duration_seconds

    db.close()

    return {
        "total_screen_time_seconds": total_seconds,
        "incidents_today": 0
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

    rows = db.query(AppUsage).filter(
        AppUsage.device_id == device_id
    ).all()

    db.close()

    ignore_packages = [
        "com.android.systemui",
        "com.google.android.apps.nexuslauncher",
        "com.android.launcher3"
    ]

    app_totals = {}

    for r in rows:

        if r.package_name in ignore_packages:
            continue

        app_totals[r.package_name] = app_totals.get(r.package_name, 0) + r.duration_seconds

    total_time = sum(app_totals.values())

    return {
        "total_screen_time": total_time,
        "apps": [
            {
                "package": pkg,
                "duration": duration
            }
            for pkg, duration in app_totals.items()
        ]
    }
    

from datetime import datetime

@app.get("/top-apps/{device_id}")
def top_apps(device_id: str):

    db = SessionLocal()

    today_start = int(datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp() * 1000)

    usage = db.query(AppUsage).filter(
        AppUsage.device_id == device_id,
        AppUsage.started_at >= today_start
    ).all()

    db.close()

    ignore_packages = [
        "com.android.systemui",
        "com.google.android.apps.nexuslauncher",
        "com.android.launcher3"
    ]

    app_time = {}

    for u in usage:

        if u.package_name in ignore_packages:
            continue

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
def save_apps(data: dict = Body(...)):
    device_id = data.get("device_id")
    apps = data.get("apps", [])

    print(f"Received installed apps for device {device_id} → {len(apps)} apps")

    if not device_id or not apps:
        print("ERROR: Missing device_id or apps")
        return {"status": "error", "message": "missing data"}

    db = SessionLocal()

    try:
        for app in apps:
            package_name = app.get("package")
            app_name = app.get("name")

            if not package_name:
                continue

            exists = db.query(InstalledApp).filter(
                InstalledApp.device_id == device_id,
                InstalledApp.package_name == package_name
            ).first()

            if not exists:
                new_app = InstalledApp(
                    device_id=device_id,
                    package_name=package_name,
                    app_name=app_name or package_name
                )
                db.add(new_app)

        db.commit()
        print(f"✅ Saved {len(apps)} installed apps for device {device_id}")
        return {"status": "saved", "count": len(apps)}

    except Exception as e:
        db.rollback()
        print(f"❌ DATABASE ERROR while saving apps: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()

@app.get("/apps/{device_id}")
def get_apps(device_id: str):

    db = SessionLocal()

    installed = db.query(InstalledApp).filter(
        InstalledApp.device_id == device_id
    ).all()

    blocked = db.query(BlockedApp).filter(
        BlockedApp.device_id == device_id
    ).all()

    blocked_set = {b.package_name for b in blocked}

    result = []

    for app in installed:

        result.append({
            "name": app.app_name,
            "package": app.package_name,
            "blocked": app.package_name in blocked_set
        })

    db.close()

    return {"apps": result}

    
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





@app.get("/usage-summary/{device_id}")
def usage_summary(device_id: str):

    db = SessionLocal()

    try:

        today = datetime.utcnow().date()

        rows = db.query(AppUsage).filter(
            AppUsage.device_id == device_id
        ).all()

        ignore = [
            "com.android.systemui",
            "com.google.android.apps.nexuslauncher",
            "com.android.launcher",
            "com.example.childcontrol"
        ]

        app_totals = {}

        for r in rows:

            ts = None

            try:
                # milliseconds timestamp
                ts = datetime.utcfromtimestamp(int(r.started_at) / 1000)
            except:
                try:
                    ts = datetime.fromisoformat(str(r.started_at))
                except:
                    continue

            if ts.date() != today:
                continue

            if r.package_name in ignore:
                continue

            app_totals[r.package_name] = app_totals.get(
                r.package_name, 0
            ) + (r.duration_seconds or 0)

        apps = [
            {
                "package_name": pkg,
                "total_seconds": sec
            }
            for pkg, sec in app_totals.items()
        ]

        return {
            "total_screen_time": sum(app_totals.values()),
            "apps": apps
        }

    finally:
        db.close()
        
Base.metadata.create_all(bind=engine)