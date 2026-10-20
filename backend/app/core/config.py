from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Resolve .env from the project root so uvicorn works from any directory
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

SQLITE_DEFAULT = "sqlite:///./app.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_name: str = "FastAPI Boilerplate"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # What the running app connects with. On Neon this is the pooled (PgBouncer) string.
    # Blank falls back to local SQLite.
    database_url: str = SQLITE_DEFAULT
    # Neon's direct connection, used only by Alembic migrations
    database_url_unpooled: str = ""

    # Signs OAuth state and derives the key that encrypts Google tokens at rest
    secret_key: str = "change-me"
    # Sliding window: every active day pushes expiry out to this many days again
    session_days: int = 90
    session_cookie_name: str = "session"

    # Where the Next.js app lives; Google sign-in redirects back here
    frontend_url: str = "http://localhost:3000"

    # Google Cloud OAuth client, see GOOGLE_SETUP.md
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Read from the CORS env var as a comma-separated string
    cors: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("cors", mode="before")
    @classmethod
    def split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def blank_database_url(cls, value: object) -> object:
        # .env.example ships DATABASE_URL="" until Neon fills it in
        return value or SQLITE_DEFAULT

    @field_validator("database_url", "database_url_unpooled")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Providers hand out postgres:// or postgresql://, which SQLAlchemy maps to psycopg2
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @model_validator(mode="after")
    def reject_default_secret_in_prod(self) -> "Settings":
        if self.environment == "production" and self.secret_key == "change-me":
            raise ValueError("SECRET_KEY must be set in production")
        return self

    @property
    def migration_database_url(self) -> str:
        return self.database_url_unpooled or self.database_url

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()
