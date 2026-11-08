from datetime import datetime
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration de base (développement)."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-a-changer")

    # SQLite en développement, PostgreSQL en production via DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "pfe.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Dépôt des livrables
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 Mo maximum
    ALLOWED_EXTENSIONS = {"pdf", "zip"}
    # Règles des vœux
    DATE_CLOTURE_VOEUX = datetime(2026, 11, 15, 23, 59)
    DATE_LIMITE_DEPOT = datetime(2026, 12, 11, 23, 59)
    MAX_VOEUX = 5   # nombre maximal de sujets dans la liste
    MIN_VOEUX = 1   # nombre minimal pour pouvoir valider


class TestConfig(Config):
    """Configuration utilisée par pytest : base en mémoire, CSRF désactivé."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    DATE_CLOTURE_VOEUX = datetime(2999, 12, 31)
    DATE_LIMITE_DEPOT = datetime(2999, 12, 31)