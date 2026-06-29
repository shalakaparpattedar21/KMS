# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # ── Google OAuth ───────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # ── Session ────────────────────────────────────────────────────────────────
    SESSION_SECRET: str

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── AI — Gemini ────────────────────────────────────────────────────────────
    # Used for: LLM responses (gemini-2.5-flash) AND embeddings (text-embedding-004)
    # Required in production. App starts without it but all AI features return errors.
    GEMINI_API_KEY: str = ""

    # ── Deployment ─────────────────────────────────────────────────────────────
    # URL of the frontend — used for CORS and OAuth post-login redirect.
    # Local dev:   http://localhost:5173
    # Production:  https://your-app.vercel.app
    FRONTEND_URL: str = "http://localhost:5173"

    # Set to True on Render (HTTPS). Keep False for local dev (HTTP).
    # Required for SameSite=None cookies to work in production.
    HTTPS_ONLY: bool = False

    # Path to Chroma persistent storage.
    # Local dev:   default (backend/chroma_db)
    # Production:  set to Render Disk mount path e.g. /var/data/chroma_db
    CHROMA_DB_PATH: str = ""

    class Config:
        env_file = ".env"


settings = Settings()