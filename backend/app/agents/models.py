from dataclasses import dataclass


@dataclass
class Citation:
    source_id: str
    doc_id: str
    title: str
