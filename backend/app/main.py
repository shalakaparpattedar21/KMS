from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth.google import router as google_router
from app.core.config import settings
from app.database.init_db import init_db
from app.api.documents.routes import router as documents_router
from app.api.sync.routes import router as sync_router
from app.api.documents.routes import router as documents_router

app = FastAPI()
app.include_router(documents_router)
app.include_router(sync_router)
app.include_router(documents_router)
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
