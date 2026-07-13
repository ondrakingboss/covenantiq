from __future__ import annotations

import os


LOCAL_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def environment_name() -> str:
    return os.environ.get("ENVIRONMENT", "development").strip().lower()


def cors_origins() -> list[str]:
    """Return explicit browser origins; production never defaults to localhost or '*'."""
    configured = os.environ.get("CORS_ORIGINS", "")
    if configured.strip():
        return list(dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in configured.split(",")
            if origin.strip()
        ))
    if environment_name() == "production":
        return []
    return list(LOCAL_CORS_ORIGINS)
