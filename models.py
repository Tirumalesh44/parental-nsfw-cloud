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

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String, index=True, nullable=False)

    timestamp = Column(String, index=True, nullable=False)

    sexual_score = Column(Float, nullable=False)
    violent_score = Column(Float, nullable=False)

    categories = Column(String, nullable=False)