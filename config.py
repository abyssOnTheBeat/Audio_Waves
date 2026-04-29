from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'beatshop.db'
UPLOAD_PREVIEWS = BASE_DIR / 'static' / 'uploads' / 'previews'
UPLOAD_COVERS = BASE_DIR / 'static' / 'uploads' / 'covers'

ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_IMAGES = {'png', 'jpg', 'jpeg', 'webp'}


class Config:
    SECRET_KEY = 'audio_waves_secret_key'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024


def prepare_folders():
    UPLOAD_PREVIEWS.mkdir(parents=True, exist_ok=True)
    UPLOAD_COVERS.mkdir(parents=True, exist_ok=True)
