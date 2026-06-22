from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth.google import router as google_router
from app.core.config import settings
from app.database.init_db import init_db
from fastapi import FastAPI, Request
from app.api.sync.routes import router as sync_router
from app.api.documents.routes import router as documents_router
from app.api.search.routes import router as search_router
from app.api.chat.routes import router as chat_router
from app.api.gmail.routes import ( router as gmail_router)
from app.api.gmail.actions import router as gmail_actions_router
from app.api.gmail.email_details import (router as gmail_email_router)

app = FastAPI()
app.include_router(documents_router)
app.include_router(sync_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(gmail_router)
app.include_router(gmail_actions_router)
app.include_router(gmail_email_router)
@app.on_event("startup")
async def startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET
)

app.include_router(
    google_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

@app.get("/")
def root():
    return {"message": "working"}

from app.api.drive.routes import router as drive_router

app.include_router(
    drive_router,
    prefix="/api/drive",
    tags=["Drive"]
)
@app.get("/session-test")
def session_test(request: Request):

    request.session["test"] = "hello"

    return {
        "session": request.session.get("test")
    }