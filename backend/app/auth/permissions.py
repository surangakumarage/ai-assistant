from app.auth.models import Role

# Mirrors the assignment's RBAC table: Viewer gets chat/search only, Analyst
# adds analytics + MCP tools, Administrator gets everything.
TOOL_PERMISSIONS: dict[str, set[Role]] = {
    "chat": {Role.VIEWER, Role.ANALYST, Role.ADMINISTRATOR},
    "search": {Role.VIEWER, Role.ANALYST, Role.ADMINISTRATOR},
    "analytics": {Role.ANALYST, Role.ADMINISTRATOR},
    "mcp": {Role.ANALYST, Role.ADMINISTRATOR},
    "admin": {Role.ADMINISTRATOR},
}


def tool_allowed(tool: str, role: Role) -> bool:
    return role in TOOL_PERMISSIONS.get(tool, set())


# Document access ceiling per role. The current sample corpus only uses
# "internal", so this has no visible effect on it today - it's real
# enforcement infrastructure for when the corpus gains tiered access levels,
# not a no-op left for later.
ROLE_MAX_ACCESS_LEVEL: dict[Role, str] = {
    Role.VIEWER: "internal",
    Role.ANALYST: "confidential",
    Role.ADMINISTRATOR: "restricted",
}


def max_access_level(role: Role) -> str:
    return ROLE_MAX_ACCESS_LEVEL.get(role, "public")
