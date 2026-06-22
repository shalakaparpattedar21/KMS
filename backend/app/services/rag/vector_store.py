import os
import logging
import chromadb

logger = logging.getLogger(__name__)

# Resolve chroma_db to an absolute path so the store does not depend on the
# process CWD. The folder lives at <repo-root>/backend/chroma_db.
_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

CHROMA_PATH = os.environ.get(
    "CHROMA_DB_PATH",
    os.path.join(_BACKEND_ROOT, "chroma_db"),
)

logger.info(f"[VECTOR_STORE] Using Chroma persistent path: {CHROMA_PATH}")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name="enterprise_kms")

try:
    _count = collection.count()
    logger.info(
        f"[VECTOR_STORE] Collection 'enterprise_kms' loaded with {_count} vectors"
    )
except Exception as _e:
    logger.warning(f"[VECTOR_STORE] Could not count collection: {_e}")