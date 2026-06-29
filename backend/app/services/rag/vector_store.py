# app/services/rag/vector_store.py
#
# PRODUCTION NOTE — Chroma persistence on Render:
#
# Render's free/starter tier uses ephemeral storage. The filesystem is wiped
# on every deploy. This means a PersistentClient pointing to a local path
# will lose all vectors on each deployment.
#
# Strategy options (in order of preference):
#
#   1. CHROMA_DB_PATH=/var/data/chroma_db
#      Use a Render Disk (persistent volume). Add a disk to your Render
#      service and set CHROMA_DB_PATH to its mount path. Vectors survive
#      deploys. RECOMMENDED for production.
#
#   2. Re-index on startup (current fallback behaviour)
#      If no disk is attached, vectors are rebuilt from PostgreSQL content
#      on each deploy via POST /api/sync/reindex-documents and
#      POST /api/gmail/reindex-emails. This is slow but functional.
#
#   3. Chroma Cloud / external Chroma server
#      For larger datasets, point CHROMA_HOST to a hosted Chroma instance.
#      (Not implemented here — add if scale requires it.)
#
# CHROMA_DB_PATH defaults to backend/chroma_db (works locally).
# Set it to your Render Disk mount path in production.

import logging
import os

import chromadb

logger = logging.getLogger(__name__)

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

CHROMA_PATH = os.environ.get(
    "CHROMA_DB_PATH",
    os.path.join(_BACKEND_ROOT, "chroma_db"),
)

logger.info(f"[VECTOR_STORE] Chroma path: {CHROMA_PATH}")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="enterprise_kms")

try:
    _count = collection.count()
    logger.info(
        f"[VECTOR_STORE] Collection 'enterprise_kms' ready — {_count} vectors"
    )
except Exception as _e:
    logger.warning(f"[VECTOR_STORE] Could not count collection: {_e}")