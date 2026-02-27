from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SEO Agency"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./data/seo_agency.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption key for API keys (Fernet)
    ENCRYPTION_KEY: str = ""  # Generate with: from cryptography.fernet import Fernet; Fernet.generate_key()

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent  # /Users/akj/seo-test
    SCRIPTS_DIR: Path = PROJECT_ROOT / "scripts"
    REFERENCES_DIR: Path = PROJECT_ROOT / "seo" / "references"
    SCHEMA_TEMPLATES: Path = PROJECT_ROOT / "schema" / "templates.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
