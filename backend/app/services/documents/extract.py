from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)