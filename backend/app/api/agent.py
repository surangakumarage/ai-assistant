import json
from dataclasses import asdict, is_dataclass

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.graph import get_agent_graph
from app.auth.dependencies import enforce_rate_limit, require_permission
from app.auth.models import User
from app.core.error_handling import friendly_error
from app.guardrails.input_validation import InvalidRequestError, validate_department, validate_question

router = APIRouter()


class AgentQueryRequest(BaseModel):
    question: str
    department: str | None = None
    top_k: int = 5


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    text: str
    access_level: str
    dense_score: float
    sparse_score: float
    hybrid_score: float


class CitationResponse(BaseModel):
    source_id: str
    doc_id: str
    title: str


class AgentQueryResponse(BaseModel):
    question: str
    intent: str
    answer: str
    citations: list[CitationResponse]
    citations_dropped: list[str] = []
    flagged_sources: list[str] = []
    results: list[RetrievedChunkResponse]
    research_summary: str | None = None
    batch_findings: list[str] = []


def _validated_request(request: AgentQueryRequest) -> AgentQueryRequest:
    try:
        question = validate_question(request.question)
        department = validate_department(request.department)
    except InvalidRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return request.model_copy(update={"question": question, "department": department})


def _initial_state(request: AgentQueryRequest, user: User) -> dict:
    return {
        "question": request.question,
        "department": request.department,
        "top_k": request.top_k,
        "role": user.role.value,
        "intent": "",
        "results": [],
        "research_summary": None,
        "batch_findings": [],
        "answer": "",
        "citations": [],
        "citations_dropped": [],
        "flagged_sources": [],
    }


def _trace_config(user: User, request: AgentQueryRequest) -> dict:
    return {
        "run_name": "agent_query",
        "tags": ["agent-graph"],
        "metadata": {
            "role": user.role.value,
            "username": user.username,
            "department": request.department,
        },
    }


def _serialize(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


@router.post("/agent/query", response_model=AgentQueryResponse)
async def agent_query(
    request: AgentQueryRequest,
    user: User = Depends(require_permission("search")),
    _: User = Depends(enforce_rate_limit),
) -> AgentQueryResponse:
    request = _validated_request(request)
    graph = get_agent_graph()
    try:
        final_state = await graph.ainvoke(_initial_state(request, user), config=_trace_config(user, request))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=friendly_error(exc)) from exc
    return AgentQueryResponse(
        question=request.question,
        intent=final_state["intent"],
        answer=final_state["answer"],
        citations=[CitationResponse(**asdict(citation)) for citation in final_state["citations"]],
        citations_dropped=final_state.get("citations_dropped", []),
        flagged_sources=final_state.get("flagged_sources", []),
        results=[RetrievedChunkResponse(**asdict(chunk)) for chunk in final_state["results"]],
        research_summary=final_state.get("research_summary"),
        batch_findings=final_state.get("batch_findings", []),
    )


@router.post("/agent/query/stream")
async def agent_query_stream(
    request: AgentQueryRequest,
    user: User = Depends(require_permission("search")),
    _: User = Depends(enforce_rate_limit),
) -> StreamingResponse:
    request = _validated_request(request)
    graph = get_agent_graph()
    initial_state = _initial_state(request, user)
    trace_config = _trace_config(user, request)

    async def event_stream():
        try:
            async for update in graph.astream(initial_state, config=trace_config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    event = {"node": node_name, "update": _serialize(node_output)}
                    yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            error_event = {"error": friendly_error(exc)}
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
            return
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
