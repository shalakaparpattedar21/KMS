from fastapi import APIRouter, Request

from app.services.google_drive.drive_service import DriveService

router = APIRouter()


@router.get("/files")
async def get_files(request: Request):

    access_token = request.session.get("access_token")

    if not access_token:
        return {
            "error": "Not authenticated"
        }

    return DriveService.get_files(access_token)