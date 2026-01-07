from app.models import SessionLocal, Script, Video

def check_db():
    db = SessionLocal()
    scripts = db.query(Script).all()
    videos = db.query(Video).all()
    print(f"Total Scripts: {len(scripts)}")
    for s in scripts:
        print(f"Script {s.id}: {s.title} (Type: {s.type})")
        
    print(f"Total Videos: {len(videos)}")
    db.close()

if __name__ == "__main__":
    check_db()
