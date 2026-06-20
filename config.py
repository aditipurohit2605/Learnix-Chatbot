import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    # Flask
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "learnix-secret-key"
    )

    # Base Directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload Settings
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Gemini API (set via environment variable — never hardcode keys)
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    GOOGLE_MODEL = os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash")

    # Allowed File Types
    ALLOWED_EXTENSIONS = {
        "document": {
            "pdf",
            "docx",
            "txt"
        },
        "avatar": {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "webp"
        }
    }

    @staticmethod
    def init_app(app):
        folders = [
            os.path.join(Config.BASE_DIR, "instance"),
            Config.UPLOAD_FOLDER,
            os.path.join(Config.UPLOAD_FOLDER, "avatars"),
            os.path.join(Config.UPLOAD_FOLDER, "materials"),
            os.path.join(Config.UPLOAD_FOLDER, "resumes"),
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)