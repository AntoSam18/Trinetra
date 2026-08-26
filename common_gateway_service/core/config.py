from pathlib import Path
from dataclasses import dataclass
import os

from dotenv import load_dotenv


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]

# Prefer a service-local .env (for separate deploy), fallback to repo-root .env (monorepo dev).
load_dotenv(SERVICE_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db_name: str
    auth_secret: str
    frontend_origin: str
    environment: str
    redis_url: str
    redis_default_ttl_seconds: int
    redis_connect_timeout_seconds: float
    redis_socket_timeout_seconds: float
    cookie_domain: str
    cookie_samesite: str
    cookie_secure: bool

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def get_settings() -> Settings:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip() or "mongodb://localhost:27017"

    redis_url = os.getenv("REDIS_URL", "").strip()
    redis_ttl = int(os.getenv("REDIS_DEFAULT_TTL_SECONDS", "30").strip() or "30")
    redis_connect_timeout = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "1.0").strip() or "1.0")
    redis_socket_timeout = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "1.5").strip() or "1.5")

    cookie_domain = os.getenv("COOKIE_DOMAIN", "").strip()
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").strip().lower() or "lax"
    cookie_secure_env = os.getenv("COOKIE_SECURE", "").strip().lower()
    if cookie_secure_env in {"1", "true", "yes", "y"}:
        cookie_secure = True
    elif cookie_secure_env in {"0", "false", "no", "n"}:
        cookie_secure = False
    else:
        cookie_secure = os.getenv("ENVIRONMENT", "development").strip().lower() == "production"

    return Settings(
        mongodb_uri=mongodb_uri,
        mongodb_db_name=os.getenv("MONGODB_DB_NAME", "trinetra").strip() or "trinetra",
        auth_secret=os.getenv("AUTH_SECRET", "dev-insecure-change-me").strip(),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").strip(),
        environment=os.getenv("ENVIRONMENT", "development").strip(),
        redis_url=redis_url,
        redis_default_ttl_seconds=max(1, redis_ttl),
        redis_connect_timeout_seconds=max(0.1, redis_connect_timeout),
        redis_socket_timeout_seconds=max(0.1, redis_socket_timeout),
        cookie_domain=cookie_domain,
        cookie_samesite=cookie_samesite,
        cookie_secure=cookie_secure,
    )


settings = get_settings()

