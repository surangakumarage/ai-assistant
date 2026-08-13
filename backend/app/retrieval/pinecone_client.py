from functools import lru_cache

from pinecone import Index, Pinecone

from app.core.config import get_settings


@lru_cache
def get_pinecone_index() -> Index:
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)
