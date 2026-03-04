# from sqlalchemy import Column, Integer, String, Float
# from database import Base

# class Detection(Base):
#     __tablename__ = "detections"

#     id = Column(Integer, primary_key=True, index=True)
#     timestamp = Column(String, index=True)
#     sexual_score = Column(Float)
#     violent_score = Column(Float)
#     categories = Column(String)


#---------------SECOND---------------#

# from sqlalchemy import Column, Integer, String, Float
# from database import Base

# class Detection(Base):
#     __tablename__ = "detections"

#     id = Column(Integer, primary_key=True, index=True)

#     device_id = Column(String, index=True)  # 🔥 CRITICAL

#     timestamp = Column(String, index=True)

#     sexual_score = Column(Float)
#     violent_score = Column(Float)

#     categories = Column(String)


#---------THIRD-----------#
from sqlalchemy import Column, Integer, String, Float
from database import Base


# =========================
# DETECTION TABLE
# =========================

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    timestamp = Column(String, index=True, nullable=False)

    sexual_score = Column(Float, nullable=False)
    violent_score = Column(Float, nullable=False)

    categories = Column(String, nullable=False)


# =========================
# INCIDENT TABLE
# =========================

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    started_at = Column(String, nullable=False)
    ended_at = Column(String, nullable=True)

    peak_risk = Column(Float, nullable=False)

    status = Column(String, nullable=False)  # ACTIVE / CLOSED
    
class ParentDevice(Base):
    __tablename__ = "parent_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    fcm_token = Column(String, nullable=False)
    
    
# =========================
# APP USAGE TABLE
# =========================

class AppUsage(Base):
    __tablename__ = "app_usage"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    package_name = Column(String, nullable=False)

    started_at = Column(String, nullable=False)
    ended_at = Column(String, nullable=False)

    duration_seconds = Column(Integer, nullable=False)


# =========================
# DEVICE COMMAND TABLE
# =========================

class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    command_type = Column(String, nullable=False)  # LOCK / UNLOCK / LIMIT

    payload = Column(String, nullable=True)

    status = Column(String, nullable=False)  # PENDING / EXECUTED

    created_at = Column(String, nullable=False)

    executed_at = Column(String, nullable=True)
    
class ScreenLimit(Base):
    __tablename__ = "screen_limits"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    daily_limit_minutes = Column(Integer)