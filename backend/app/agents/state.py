from typing import TypedDict

from app.agents.models import Citation
from app.retrieval.hybrid_search import RetrievedChunk


class AgentState(TypedDict):
    question: str
    department: str | None
    top_k: int
    role: str
    intent: str
    results: list[RetrievedChunk]
    research_summary: str | None
    batch_findings: list[str]
    answer: str
    citations: list[Citation]
    citations_dropped: list[str]
    flagged_sources: list[str]
