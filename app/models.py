from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import DATABASE_URL

Base = declarative_base()

class Bike(Base):
    __tablename__ = 'bikes'
    
    id = Column(Integer, primary_key=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    category = Column(String) # e.g., Sport, Cruiser, Scooter
    specifications = Column(JSON) # Engine, Power, Torque, Mileage, etc.
    last_featured_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scripts = relationship("Script", back_populates="bike")

class Script(Base):
    __tablename__ = 'scripts'

    id = Column(Integer, primary_key=True)
    bike_id = Column(Integer, ForeignKey('bikes.id'))
    type = Column(String, nullable=False) # 'long' or 'shorts'
    title = Column(String)
    content = Column(JSON) # Structured content: {hook, intro, sections: [{text, visual_keywords}], outro}
    created_at = Column(DateTime, default=datetime.utcnow)

    bike = relationship("Bike", back_populates="scripts")
    video = relationship("Video", back_populates="script", uselist=False)

class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey('scripts.id'))
    filepath = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow)

    script = relationship("Script", back_populates="video")
    upload_log = relationship("UploadLog", back_populates="video", uselist=False)

class UploadLog(Base):
    __tablename__ = 'upload_logs'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    youtube_id = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # 'success', 'failed'

    video = relationship("Video", back_populates="upload_log")

# Database Initialization
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
