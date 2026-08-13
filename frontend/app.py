import json
import os

import httpx
import streamlit as st

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")

NODE_LABELS = {
    "supervisor": "Supervisor",
    "retrieval": "Retrieval",
    "research": "Research",
    "response": "Response",
}

st.set_page_config(page_title="Enterprise AI Assistant", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []


def login(username: str, password: str) -> bool:
    try:
        response = httpx.post(
            f"{BACKEND_BASE_URL}/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        st.error(f"Could not reach backend: {exc}")
        return False

    if response.status_code != 200:
        st.error("Invalid username or password.")
        return False

    payload = response.json()
    st.session_state.token = payload["access_token"]
    st.session_state.role = payload["role"]
    st.session_state.username = username
    return True


def logout() -> None:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.messages = []


def describe_event(node: str, update: dict) -> str:
    if node == "supervisor":
        return f"Routed question to **{update.get('intent', '?')}**"
    if node == "retrieval":
        results = update.get("results", [])
        return f"Hybrid search (dense + BM25) returned **{len(results)}** chunks"
    if node == "research":
        results = update.get("results", [])
        findings = update.get("batch_findings", [])
        return (
            f"Explored **{len(results)}** candidate chunks across documents, "
            f"decomposed into per-document sub-agent calls, **{len(findings)}** relevant findings kept"
        )
    if node == "response":
        citations = update.get("citations", [])
        dropped = update.get("citations_dropped", [])
        flagged = update.get("flagged_sources", [])
        line = f"Answer generated with **{len(citations)}** verified citation(s)"
        if dropped:
            line += f" — rejected **{len(dropped)}** unverified citation id(s) as a hallucination guardrail"
        if flagged:
            line += f" — ⚠️ **{len(flagged)}** source(s) flagged for instruction-like phrasing (prompt-injection guardrail)"
        return line
    return "State updated"


def run_query(question: str, department: str | None, activity_placeholder) -> dict:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    payload = {"question": question, "department": department or None, "top_k": 5}

    events: list[tuple[str, dict]] = []
    final_update: dict = {}

    with httpx.stream(
        "POST",
        f"{BACKEND_BASE_URL}/agent/query/stream",
        json=payload,
        headers=headers,
        timeout=120,
    ) as response:
        if response.status_code != 200:
            response.read()
            raise RuntimeError(f"Agent request failed ({response.status_code}): {response.text}")

        current_event = "message"
        for line in response.iter_lines():
            if line == "":
                current_event = "message"
                continue
            if line.startswith("event: "):
                current_event = line[len("event: ") :].strip()
                continue
            if not line.startswith("data: "):
                continue

            payload = line[len("data: ") :]
            if current_event == "error":
                data = json.loads(payload)
                raise RuntimeError(data.get("error", "The agent failed to process this request."))
            if current_event != "message":
                continue

            data = json.loads(payload)
            if "node" not in data:
                continue
            node = data["node"]
            update = data["update"]
            events.append((node, update))
            final_update.update(update)

            with activity_placeholder.container():
                for evt_node, evt_update in events:
                    st.markdown(f"**{NODE_LABELS.get(evt_node, evt_node)}**")
                    st.caption(describe_event(evt_node, evt_update))

    return final_update


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})"):
        for citation in citations:
            st.markdown(f"- {citation['title']} (`{citation['source_id']}`)")


# --- Login gate ---
if not st.session_state.token:
    st.title("Enterprise AI Assistant — Sign in")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if login(username, password):
            st.rerun()
    st.caption("Demo users: viewer/viewer123, analyst/analyst123, admin/admin123")
    st.stop()

# --- Main app ---
with st.sidebar:
    st.markdown(f"**User:** {st.session_state.username}")
    st.markdown(f"**Role:** {st.session_state.role}")
    department = st.text_input("Department filter (optional)", value="")
    if st.button("Log out"):
        logout()
        st.rerun()

st.title("Enterprise AI Assistant")

chat_col, activity_col = st.columns([2, 1])

with chat_col:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_citations(message.get("citations", []))

with activity_col:
    st.markdown("### Agent Activity Panel")
    idle_placeholder = st.empty()
    if not st.session_state.messages:
        idle_placeholder.caption("Ask a question to see the agent's steps here.")

question = st.chat_input("Ask about internal documents...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with chat_col:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with activity_col:
                idle_placeholder.empty()
                activity_placeholder = st.empty()
            answer_placeholder = st.empty()

            try:
                final_update = run_query(question, department, activity_placeholder)
                answer = final_update.get("answer") or "(no answer produced)"
                citations = final_update.get("citations", [])
            except RuntimeError as exc:
                answer = f"Error: {exc}"
                citations = []

            answer_placeholder.markdown(answer)
            render_citations(citations)

    st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
