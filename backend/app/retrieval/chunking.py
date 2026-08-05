from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    text: str


def chunk_document(doc_id: str, text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return [
        Chunk(chunk_id=f"{doc_id}::chunk-{i}", chunk_index=i, text=piece)
        for i, piece in enumerate(splitter.split_text(text))
    ]
