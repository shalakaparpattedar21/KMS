from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import requests
from app.models.user import User
from app.database.session import SessionLocal
from app.core.config import settings
from app.models.email import Email
from app.models.document import Document
from app.models.document_content import DocumentContent


router = APIRouter()

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
    "scope": (
        "openid "
        "email "
        "profile "
        "https://www.googleapis.com/auth/drive.readonly "
        "https://www.googleapis.com/auth/gmail.modify "
        "https://www.googleapis.com/auth/gmail.compose "
    )
}
)

@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(
        request,
        settings.GOOGLE_REDIRECT_URI
    )
@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):

    token = await oauth.google.authorize_access_token(
    request
    )

    print("FULL TOKEN:", token)

    user = token.get("userinfo")

    request.session["access_token"] = token["access_token"]

    if user:

        email = user.get("email")
        name = user.get("name")
        google_id = user.get("sub")

        request.session["user_email"] = email
        request.session["user_name"] = name
        request.session["google_id"] = google_id

        db = SessionLocal()

        try:

            existing_user = (
                db.query(User)
                .filter(
                    User.google_id == google_id
                )
                .first()
            )

            if not existing_user:

                new_user = User(
                    google_id=google_id,
                    email=email,
                    name=name
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                existing_user = new_user

            request.session["user_id"] = (
                existing_user.id
            )

        finally:
            db.close()

    return RedirectResponse(
        url="http://localhost:5173/dashboard"
    )
@router.get("/me")
async def me(request: Request):

    return {
        "user_id": request.session.get(
            "user_id"
        ),
        "email": request.session.get(
            "user_email"
        ),
        "name": request.session.get(
            "user_name"
        ),
        "google_id": request.session.get(
            "google_id"
        )
    }
@router.get("/token")
def get_token(request: Request):
    return {
        "token_exists": request.session.get("access_token") is not None,
        "token": request.session.get("access_token")
    }
@router.get("/userinfo")
async def userinfo(request: Request):

    access_token = request.session.get(
        "access_token"
    )

    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response.json()
@router.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return {
        "message": "Logged out"
    }
@router.post("/disconnect")
async def disconnect_google(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    db = SessionLocal()

    try:

        if user_id:

            user_documents = (
                db.query(Document)
                .filter(
                    Document.user_id == user_id
                )
                .all()
            )

            document_ids = [
                doc.id
                for doc in user_documents
            ]

            if document_ids:

                db.query(DocumentContent).filter(
                    DocumentContent.document_id.in_(document_ids)
                ).delete(
                    synchronize_session=False
                )

            db.query(Document).filter(
                Document.user_id == user_id
            ).delete()

            db.query(Email).filter(
                Email.user_id == user_id
            ).delete()

            db.commit()

    finally:

        db.close()

    request.session.clear()

    return {
        "message": "Google account disconnected"
    }