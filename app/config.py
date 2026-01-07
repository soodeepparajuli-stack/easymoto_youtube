import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "easymoto.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

# Generation Config
DAILY_LONG_VIDEO_COUNT = 1
DAILY_SHORTS_COUNT = 2

# Video Settings
LONG_VIDEO_SIZE = (1920, 1080)
SHORTS_SIZE = (1080, 1920)
FPS = 30
DRY_RUN = False # Set to False to enable uploads (Default)

