from functools import lru_cache

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.research_agent import research_node
from app.agents.response_agent import response_node
from app.agents.retrieval_agent import retrieval_node
from app.agents.state import AgentState
from app.agents.supervisor import DEEP_RESEARCH, KNOWLEDGE_SEARCH, route_from_supervisor, supervisor_node


@lru_cache
def get_agent_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("research", research_node)
    graph.add_node("response", response_node)
    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {KNOWLEDGE_SEARCH: "retrieval", DEEP_RESEARCH: "research"},
    )
    graph.add_edge("retrieval", "response")
    graph.add_edge("research", "response")
    graph.add_edge("response", END)
    return graph.compile()
