import json
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "docs" / "manifest.json"


@dataclass
class DocumentRecord:
    doc_id: str
    title: str
    document_type: str
    department: str
    access_level: str
    created_date: str
    path: Path
    text: str


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def load_documents() -> list[DocumentRecord]:
    records = []
    for entry in load_manifest():
        path = REPO_ROOT / entry["path"]
        records.append(
            DocumentRecord(
                doc_id=entry["doc_id"],
                title=entry["title"],
                document_type=entry["document_type"],
                department=entry["department"],
                access_level=entry["access_level"],
                created_date=entry["created_date"],
                path=path,
                text=extract_pdf_text(path),
            )
        )
    return records
