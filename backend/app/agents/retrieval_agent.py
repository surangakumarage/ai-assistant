from app.agents.state import AgentState
from app.auth.models import Role
from app.auth.permissions import max_access_level
from app.retrieval.hybrid_search import hybrid_search


async def retrieval_node(state: AgentState) -> AgentState:
    results = await hybrid_search(
        query=state["question"],
        department=state.get("department"),
        top_k=state.get("top_k", 5),
        max_access_level=max_access_level(Role(state["role"])),
    )
    return {**state, "results": results}
