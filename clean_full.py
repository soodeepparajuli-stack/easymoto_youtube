import os
import sys
# Add parent dir to path if needed for 'app' module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Base, engine

def clean_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully.")

if __name__ == "__main__":
    clean_db()
