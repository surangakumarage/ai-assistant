Enterprise AI Assistant - POC
==============================

Overview
--------
Enterprise-grade AI Assistant answering questions over internal organizational
documents (policies, architecture docs, runbooks, incident reports, product
specs, meeting notes). Built with LangGraph (multi-agent orchestration),
FastAPI (async backend), Streamlit (chat UI), Pinecone (hybrid vector search),
and LangSmith (observability). See PLAN.md for the full task breakdown.

Repo Structure
--------------
backend/
    app/
        api/          FastAPI routes (chat, auth, admin, documents)
        auth/         Hardcoded users, RBAC dependencies/decorators
        agents/        LangGraph graph definition, node implementations, state schema
        retrieval/     Pinecone client, dense/sparse hybrid search, reranking
        tools/         Knowledge search tool, Python analysis tool, MCP client
        guardrails/     Prompt-injection checks, citation validation, brand-safety
                        judge, tool-arg schema validation
        memory/         LangGraph checkpointer config, conversation summarization
        core/           Token-bucket rate limiter, structured logging, settings/config
    tests/              Unit + integration tests

frontend/               Streamlit chat app (chat window, login, Agent Activity Panel)

mcp_server/              Dummy MCP server (employee directory, service catalog,
                        incident records)

sample_data/             Mock enterprise documents + metadata manifest used to
                        seed the vector index

docs/                    Architecture diagram, assumptions, model-selection
                        rationale, memory-design notes, security write-up

docker-compose.yml       Runs backend + frontend + mcp_server together for local/demo use
.env.example             Template for required environment variables (tracked)
.env                     Local copy of the above with real keys (gitignored, never commit)

Status
------
Repo scaffold only at this stage - directories are in place with placeholder
Python packages (__init__.py), and requirements.txt/Dockerfile stubs exist for
backend, frontend, and mcp_server so `docker-compose up` is wired end-to-end
once app code lands. Implementation follows the build order in PLAN.md,
starting with the retrieval layer.

Setup (to be filled in as components land)
-------------------------------------------
1. Copy .env.example to .env (already done locally) and fill in real API keys
   (Anthropic, Pinecone, LangSmith). .env is gitignored - never commit it.
2. Backend: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
3. Frontend: cd frontend && streamlit run app.py
4. Or: docker-compose up   (builds backend, frontend, mcp_server together)

Notes
-----
*.md files are gitignored in this repo (see .gitignore) - project documentation
lives in this README.txt and other .txt files under docs/ instead.
