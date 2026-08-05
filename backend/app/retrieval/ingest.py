import asyncio
import logging

from app.retrieval.chunking import chunk_document
from app.retrieval.embeddings import embed_texts
from app.retrieval.loader import load_documents
from app.retrieval.pinecone_client import get_pinecone_index

logger = logging.getLogger(__name__)

EMBED_BATCH_SIZE = 100
UPSERT_BATCH_SIZE = 100


async def ingest_documents() -> None:
    index = get_pinecone_index()
    documents = load_documents()
    logger.info("Loaded %d documents from manifest", len(documents))

    index_dimension = index.describe_index_stats().dimension

    for doc in documents:
        chunks = chunk_document(doc.doc_id, doc.text)
        if not chunks:
            logger.warning("No text extracted for %s (%s), skipping", doc.doc_id, doc.path)
            continue

        vectors = []
        for batch_start in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
            batch_embeddings = await embed_texts([c.text for c in batch])

            if index_dimension and len(batch_embeddings[0]) != index_dimension:
                raise ValueError(
                    f"Embedding dimension {len(batch_embeddings[0])} does not match "
                    f"Pinecone index dimension {index_dimension}. Recreate the index "
                    f"with the matching dimension or change EMBEDDING_MODEL."
                )

            for chunk, embedding in zip(batch, batch_embeddings):
                vectors.append(
                    {
                        "id": chunk.chunk_id,
                        "values": embedding,
                        "metadata": {
                            "doc_id": doc.doc_id,
                            "title": doc.title,
                            "document_type": doc.document_type,
                            "department": doc.department,
                            "access_level": doc.access_level,
                            "created_date": doc.created_date,
                            "chunk_index": chunk.chunk_index,
                            "text": chunk.text,
                        },
                    }
                )

        for batch_start in range(0, len(vectors), UPSERT_BATCH_SIZE):
            index.upsert(
                vectors=vectors[batch_start : batch_start + UPSERT_BATCH_SIZE],
                namespace=doc.department,
            )

        logger.info(
            "Ingested %d chunks for %s into namespace '%s'", len(chunks), doc.doc_id, doc.department
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(ingest_documents())
