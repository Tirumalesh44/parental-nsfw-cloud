from fastapi import FastAPI, File, UploadFile
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Detection
from datetime import datetime
import json
import requests
import os

app = FastAPI(title="Parental Control Backend")

# Create DB tables
Base.metadata.create_all(bind=engine)

HF_TOKEN = os.getenv("HF_TOKEN")

HF_API_URL = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"

SEXUAL_THRESHOLD = 0.6


# ================= HUGGINGFACE CALL =================

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
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

    # Debug print (check Render logs)
    print("HF STATUS:", response.status_code)
    print("HF RAW RESPONSE:", response.text[:300])

    try:
        data = response.json()
    except Exception:
        return {
            "error": "Invalid JSON response",
            "raw": response.text[:300]
        }

    if isinstance(data, dict) and "error" in data:
        return {"error": data["error"]}

    return data


# ================= ANALYZE FRAME =================

@app.post("/analyze-frame")
async def analyze_frame(file: UploadFile = File(...)):

    contents = await file.read()

    hf_result = analyze_with_hf(contents)

    # If HF returned error
    if isinstance(hf_result, dict) and "error" in hf_result:
        return {
            "categories": [],
            "sexual_score": 0.0,
            "hf_error": hf_result["error"],
            "timestamp": datetime.utcnow().isoformat()
        }

    sexual_score = 0.0

    if isinstance(hf_result, list):
        for item in hf_result:
            if item["label"].lower() == "nsfw":
                sexual_score = item["score"]

    categories = []
    if sexual_score >= SEXUAL_THRESHOLD:
        categories.append("sexual")

    now = datetime.utcnow().isoformat()

    if categories:
        db: Session = SessionLocal()
        detection = Detection(
            timestamp=now,
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
        "timestamp": now
    }


# ================= SUMMARY =================

@app.get("/parent-summary")
def parent_summary():
    db: Session = SessionLocal()
    total = db.query(Detection).count()
    db.close()
    return {"total_bad_frames": total}


@app.get("/")
def health():
    return {"status": "Backend Running"}
