# app/main.py
#
# CHANGES:
#   - Replaced @app.on_event("startup") with lifespan context manager
#     (on_event is deprecated in FastAPI 0.95+ and shows a warning)
#   - Middleware order preserved (SessionMiddleware must wrap CORS)
#   - same_site="none" preserved for cross-origin cookie support
#     (Vercel frontend → Render backend requires SameSite=None; Secure)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth.google import router as google_router
from app.api.chat.routes import router as chat_router
from app.api.documents.routes import router as documents_router
from app.api.drive.routes import router as drive_router
from app.api.gmail.actions import router as gmail_actions_router
from app.api.gmail.email_details import router as gmail_email_router
from app.api.gmail.routes import router as gmail_router
from app.api.search.routes import router as search_router
from app.api.sync.routes import router as sync_router
from app.core.config import settings
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the app begins serving requests."""
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents_router)
app.include_router(sync_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(gmail_router)
app.include_router(gmail_actions_router)
app.include_router(gmail_email_router)
app.include_router(drive_router, prefix="/api/drive", tags=["Drive"])
app.include_router(google_router, prefix="/api/auth", tags=["Authentication"])


# ── Middleware ─────────────────────────────────────────────────────────────────
# ORDER MATTERS in Starlette: middleware added last runs first on incoming
# requests, so SessionMiddleware must be added AFTER CORSMiddleware so that
# sessions are available inside CORS-handled routes.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session cookie:
#   - same_site="none" is required when frontend (Vercel) and backend (Render)
#     are on different origins. Browsers block SameSite=Lax cross-site cookies.
#   - https_only must be True in production so the browser sends the cookie
#     over HTTPS. Set HTTPS_ONLY=true in Render env vars.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="session",
    max_age=8 * 60 * 60,   # 8 hours
    https_only=settings.HTTPS_ONLY,
    same_site="none",
)


@app.get("/")
def root():
    return {"message": "RIIDL KMS API running"}


@app.get("/health")
def health():
    """Health check endpoint for Render."""
    return {"status": "ok"}