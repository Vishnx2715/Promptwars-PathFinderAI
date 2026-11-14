import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PathForge AI"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "pathforge_hackathon_super_secret_jwt_key_change_in_production_32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    DATABASE_URL: str = "sqlite+aiosqlite:///./pathforge.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    # xAI Grok Settings (primary AI provider)
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_MODEL: str = "grok-4"
    AI_TIMEOUT_SECONDS: int = 25

    # Legacy OpenAI fallback (kept for backward compat — not used if XAI_API_KEY is set)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: int = 25

    # Cookie Settings
    SECURE_COOKIE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Python Execution (external provider, configurable)
    PYTHON_EXECUTION_API_URL: str = ""
    PYTHON_EXECUTION_API_KEY: str = ""

    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".zip", ".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx",
        ".html", ".css", ".json", ".pdf", ".docx",
    ]
    ALLOWED_RESUME_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
