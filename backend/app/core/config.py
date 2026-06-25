from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    SESSION_SECRET: str
    DATABASE_URL: str

    # AI — Gemini is the production LLM; optional so the app starts even if
    # the key is temporarily missing (Ollama fallback handles it in llm_service).
    GEMINI_API_KEY: str = ""

    # ---------------------------------------------------------------------------
    # Deployment config
    # ---------------------------------------------------------------------------
    # URL of the frontend — used for CORS and OAuth post-login redirect.
    # Set to https://your-app.vercel.app in Render env vars.
    FRONTEND_URL: str = "http://localhost:5173"

    # Set to True on Render (HTTPS). Keep False for local dev (HTTP).
    HTTPS_ONLY: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
