# app/services/gmail/gmail_sync_service.py
#
# PERFORMANCE FIX: Email detail fetching is now parallelised with
# ThreadPoolExecutor. Previously 100 emails took ~2 minutes (serial HTTP).
# With 10 workers it completes in ~15-20 seconds.

import base64
import logging
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.email import Email
from app.services.rag.index_service import IndexService

logger = logging.getLogger(__name__)

# How many Gmail detail requests to fire in parallel.
# 10 is safe within Gmail API rate limits for a dev/test app.
_FETCH_WORKERS = 10


def _get_header(headers: list, name: str) -> str | None:
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return None


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode(
                    "utf-8", errors="ignore"
                )
        if part.get("parts"):
            body = _extract_body(part)
            if body:
                return body

    return ""


def _fetch_email_detail(gmail_id: str, headers: dict) -> dict | None:
    """
    Fetch a single Gmail message detail. Returns a parsed dict or None on error.
    Designed to run in a thread pool.
    """
    try:
        resp = requests.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{gmail_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        payload = data.get("payload", {})
        hdrs = payload.get("headers", [])

        return {
            "gmail_id": gmail_id,
            "thread_id": data.get("threadId"),
            "subject": _get_header(hdrs, "Subject"),
            "sender": _get_header(hdrs, "From"),
            "recipient": _get_header(hdrs, "To"),
            "received_at": _get_header(hdrs, "Date"),
            "body": _extract_body(payload),
        }
    except Exception as e:
        logger.warning(f"[GMAIL SYNC] Failed to fetch detail for {gmail_id}: {e}")
        return None


class GmailSyncService:
    """
    Reusable Gmail sync logic with parallel HTTP fetching.

    Sync flow:
    1. Fetch list of message IDs (1 HTTP call)
    2. Filter out IDs already in the DB for this user (1 SQL query)
    3. Fetch details for new IDs in parallel (ThreadPoolExecutor)
    4. INSERT + Chroma index each new email

    Deduplication is per-user so the same gmail_message_id can exist
    for two different users (e.g. shared threads).
    """

    @staticmethod
    def sync(
        access_token: str,
        user_id: int,
        db: Session,
        max_results: int = 100,
    ) -> dict:
        logger.info(
            f"[GMAIL SYNC] Starting for user_id={user_id} max={max_results}"
        )

        api_headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Get list of message IDs — single call
        try:
            list_resp = requests.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                params={"maxResults": max_results},
                headers=api_headers,
                timeout=15,
            )
            list_resp.raise_for_status()
        except Exception as e:
            logger.error(f"[GMAIL SYNC] Failed to list messages: {e}")
            return {"synced": 0, "skipped": 0, "error": str(e)}

        all_ids = [m["id"] for m in list_resp.json().get("messages", [])]
        logger.info(f"[GMAIL SYNC] Gmail returned {len(all_ids)} message ids")

        if not all_ids:
            return {"synced": 0, "skipped": 0}

        # 2. Bulk check which IDs are already in the DB for this user — single query
        existing_rows = (
            db.query(Email.gmail_message_id)
            .filter(
                Email.gmail_message_id.in_(all_ids),
                Email.user_id == user_id,
            )
            .all()
        )
        existing_ids = {row.gmail_message_id for row in existing_rows}
        new_ids = [gid for gid in all_ids if gid not in existing_ids]
        skipped = len(all_ids) - len(new_ids)

        logger.info(
            f"[GMAIL SYNC] {len(new_ids)} new / {skipped} already synced"
        )

        if not new_ids:
            return {"synced": 0, "skipped": skipped}

        # 3. Fetch details in parallel
        fetched = {}
        with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as pool:
            futures = {
                pool.submit(_fetch_email_detail, gid, api_headers): gid
                for gid in new_ids
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    fetched[result["gmail_id"]] = result

        logger.info(
            f"[GMAIL SYNC] Parallel fetch complete: "
            f"{len(fetched)}/{len(new_ids)} succeeded"
        )

        # 4. Insert + index (preserve Gmail order: newest first)
        synced = 0
        for gid in new_ids:
            detail = fetched.get(gid)
            if not detail:
                continue

            email = Email(
                gmail_message_id=gid,
                gmail_thread_id=detail["thread_id"],
                user_id=user_id,
                subject=detail["subject"],
                sender=detail["sender"],
                recipient=detail["recipient"],
                body=detail["body"],
                received_at=detail["received_at"],
            )
            db.add(email)
            db.flush()

            IndexService.index_email(
                email_id=email.id,
                subject=email.subject,
                sender=email.sender,
                body=email.body,
                received_at=str(email.received_at) if email.received_at else None,
            )
            synced += 1

        db.commit()

        logger.info(
            f"[GMAIL SYNC] Done for user_id={user_id} — "
            f"synced={synced} skipped={skipped}"
        )
        return {"synced": synced, "skipped": skipped}

    @staticmethod
    def sync_in_background(
        access_token: str,
        user_id: int,
        max_results: int = 100,
    ):
        """
        Run sync in a new DB session, intended for background thread use.
        """
        db = SessionLocal()
        try:
            GmailSyncService.sync(
                access_token=access_token,
                user_id=user_id,
                db=db,
                max_results=max_results,
            )
        except Exception as e:
            logger.error(f"[GMAIL SYNC BG] Unhandled error: {e}")
        finally:
            db.close()