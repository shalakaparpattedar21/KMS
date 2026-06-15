from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.google_drive.sync_service import SyncService
router = APIRouter(
    prefix="/api/sync",
    tags=["Sync"]
)
@router.post("/start")
async def start_sync(
    request: Request,
    db: Session = Depends(get_db)
):
    access_token = request.session.get(
        "access_token"
    )
    user_id = request.session.get(
        "user_id"
    )
    if not access_token:
        return {
            "error": "Not authenticated"
        }
    count = SyncService.sync_files(
        access_token,
        user_id,
        db
    )
    return {
        "synced": count
    }   