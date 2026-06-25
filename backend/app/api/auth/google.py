# app/api/auth/google.py
#
# OAuth flow implemented manually with httpx instead of Authlib.
#
# WHY: Authlib's authorize_redirect() stores an OAuth `state` token in
# request.session, then authorize_access_token() reads it back during the
# callback. On Windows localhost, the Starlette session cookie is dropped
# between the redirect-to-Google and the callback request (same_site + http
# timing issue), so the state is gone by the time the callback arrives and
# Authlib raises MismatchingStateError.
#
# FIX: We generate and verify the state ourselves using a simple hmac, and
# pass it as a query parameter that survives the round-trip through Google
# without relying on the session cookie being present at callback time.

import hashlib
import hmac
import logging
import secrets
import threading
import urllib.parse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.services.gmail.gmail_sync_service import GmailSyncService

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Google OAuth endpoints
# ---------------------------------------------------------------------------
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

_SCOPES = " ".join([
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
])


def _make_state(nonce: str) -> str:
    """HMAC-sign a nonce with the session secret so we can verify it later."""
    sig = hmac.new(
        settings.SESSION_SECRET.encode(),
        nonce.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{nonce}.{sig}"


def _verify_state(state: str) -> bool:
    """Return True if the state was signed by us."""
    try:
        nonce, sig = state.rsplit(".", 1)
        expected = hmac.new(
            settings.SESSION_SECRET.encode(),
            nonce.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.get("/google/login")
async def google_login(request: Request):
    """
    Redirect the user to Google's OAuth consent screen.
    State is HMAC-signed — no session cookie needed to verify it.
    """
    nonce = secrets.token_urlsafe(16)
    state = _make_state(nonce)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": _SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    url = _GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=url)


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------

@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):
    """
    Google redirects here after the user approves.
    Exchange the code for tokens, save the user, start background Gmail sync.
    """
    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    error = request.query_params.get("error", "")

    # User denied access
    if error:
        logger.warning(f"[AUTH] Google returned error: {error}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=access_denied")

    # Verify our HMAC state — no session cookie required
    if not _verify_state(state):
        logger.error("[AUTH] State verification failed — possible CSRF")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=state_mismatch")

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_resp.status_code != 200:
        logger.error(f"[AUTH] Token exchange failed: {token_resp.text}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    # Fetch user info
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        logger.error(f"[AUTH] Userinfo fetch failed: {userinfo_resp.text}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=userinfo_failed")

    user_info = userinfo_resp.json()
    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("sub")

    # Save session
    request.session["access_token"] = access_token
    request.session["user_email"] = email
    request.session["user_name"] = name
    request.session["google_id"] = google_id

    # Upsert user in DB
    user_id = None
    db = SessionLocal()
    try:
        existing_user = (
            db.query(User).filter(User.google_id == google_id).first()
        )
        if not existing_user:
            new_user = User(google_id=google_id, email=email, name=name)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            existing_user = new_user

        user_id = existing_user.id
        request.session["user_id"] = user_id
        logger.info(f"[AUTH] Login success: {email} (user_id={user_id})")

    finally:
        db.close()

    # Background Gmail sync — fires immediately, redirect happens now
    if user_id and access_token:
        thread = threading.Thread(
            target=GmailSyncService.sync_in_background,
            args=(access_token, user_id),
            daemon=True,
        )
        thread.start()

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/search")


# ---------------------------------------------------------------------------
# Session / user info endpoints
# ---------------------------------------------------------------------------

@router.get("/me")
async def me(request: Request):
    return {
        "user_id": request.session.get("user_id"),
        "email": request.session.get("user_email"),
        "name": request.session.get("user_name"),
        "google_id": request.session.get("google_id"),
    }


@router.get("/token")
def get_token(request: Request):
    return {
        "token_exists": request.session.get("access_token") is not None,
        "token": request.session.get("access_token"),
    }


@router.get("/userinfo")
async def userinfo(request: Request):
    access_token = request.session.get("access_token")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    return resp.json()


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@router.get("/logout")
async def logout(request: Request):
    """
    Clear session + delete browser cookie.
    Knowledge (documents, emails, Chroma vectors) is NOT touched.
    """
    request.session.clear()
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(key="session", path="/", httponly=True, samesite="lax")
    return response


# ---------------------------------------------------------------------------
# Disconnect Google
# ---------------------------------------------------------------------------

@router.post("/disconnect")
async def disconnect_google(request: Request):
    """
    Revoke the Google OAuth token and clear the session.

    IMPORTANT — does NOT delete:
      - Documents
      - Emails
      - DocumentContent
      - Chroma embeddings

    This is a shared enterprise knowledge base.
    Knowledge synced by a user belongs to the organisation and must remain
    available after the original uploader disconnects their Google account.
    """
    access_token = request.session.get("access_token")

    # Revoke token at Google — best effort
    if access_token:
        try:
            async with httpx.AsyncClient() as client:
                revoke_resp = await client.post(
                    _GOOGLE_REVOKE_URL,
                    params={"token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            logger.info(f"[DISCONNECT] Revoke status: {revoke_resp.status_code}")
        except Exception as e:
            logger.warning(f"[DISCONNECT] Token revoke failed (non-critical): {e}")

    request.session.clear()

    response = JSONResponse({
        "message": "Google disconnected. Your synced knowledge remains in the KMS."
    })
    response.delete_cookie(key="session", path="/", httponly=True, samesite="lax")
    return response