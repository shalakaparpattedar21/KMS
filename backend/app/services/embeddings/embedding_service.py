# backend/app/services/embeddings/embedding_service.py

from chromadb.utils import embedding_functions

_ef = embedding_functions.DefaultEmbeddingFunction()


class EmbeddingService:

    @staticmethod
    def embed(text: str) -> list:
        return [float(x) for x in _ef([(text or "")[:2048]])[0]]