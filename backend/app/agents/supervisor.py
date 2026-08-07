from app.agents.state import AgentState

KNOWLEDGE_SEARCH = "knowledge_search"
DEEP_RESEARCH = "deep_research"

# Simplification: routes on keyword cues rather than an LLM classification
# call, to keep the supervisor cheap and fast on every request. A question
# implying cross-document aggregation goes to the Research agent (RLM-style
# decompose/batch/aggregate); everything else goes to a direct top-k lookup.
_RESEARCH_CUES = (
    "all ",
    "summarize",
    "summarise",
    "trend",
    "recurring",
    "root cause",
    "across",
    "compare",
    "overall",
    "aggregate",
)


def _looks_like_research(question: str) -> bool:
    lowered = question.lower()
    return any(cue in lowered for cue in _RESEARCH_CUES)


async def supervisor_node(state: AgentState) -> AgentState:
    intent = DEEP_RESEARCH if _looks_like_research(state["question"]) else KNOWLEDGE_SEARCH
    return {**state, "intent": intent}


def route_from_supervisor(state: AgentState) -> str:
    return state.get("intent", KNOWLEDGE_SEARCH)
