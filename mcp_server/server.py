from mcp.server.mcpserver import MCPServer

mcp_server = MCPServer(
    name="meridian-enterprise-data",
    description=(
        "Dummy enterprise data for Meridian Commercial Bank's AI Assistant POC: "
        "employee directory, service catalog, and incident records."
    ),
)

EMPLOYEES = [
    {"employee_id": "E-1001", "name": "Alice Chen", "title": "Senior SRE", "department": "payments", "email": "alice.chen@meridianbank.example"},
    {"employee_id": "E-1002", "name": "Brian Osei", "title": "Payments Platform Lead", "department": "payments", "email": "brian.osei@meridianbank.example"},
    {"employee_id": "E-1003", "name": "Carla Ibarra", "title": "Core Banking Engineer", "department": "core_banking", "email": "carla.ibarra@meridianbank.example"},
    {"employee_id": "E-1004", "name": "David Kim", "title": "Security Engineer", "department": "security", "email": "david.kim@meridianbank.example"},
    {"employee_id": "E-1005", "name": "Elena Petrova", "title": "Data Platform Engineer", "department": "data_platform", "email": "elena.petrova@meridianbank.example"},
    {"employee_id": "E-1006", "name": "Farid Haidari", "title": "Product Manager", "department": "product", "email": "farid.haidari@meridianbank.example"},
    {"employee_id": "E-1007", "name": "Grace Lin", "title": "Retail Banking Engineer", "department": "retail_banking", "email": "grace.lin@meridianbank.example"},
    {"employee_id": "E-1008", "name": "Hassan Ali", "title": "Engineering Manager", "department": "engineering", "email": "hassan.ali@meridianbank.example"},
    {"employee_id": "E-1009", "name": "Priya Nair", "title": "Site Reliability Engineer", "department": "payments", "email": "priya.nair@meridianbank.example"},
    {"employee_id": "E-1010", "name": "Tom Walsh", "title": "Fraud Operations Analyst", "department": "security", "email": "tom.walsh@meridianbank.example"},
]

SERVICE_CATALOG = [
    {"service_id": "SVC-001", "name": "Payment Gateway", "department": "payments", "owner": "Alice Chen", "tier": "tier-1", "status": "operational"},
    {"service_id": "SVC-002", "name": "Card Authorization Service", "department": "payments", "owner": "Brian Osei", "tier": "tier-1", "status": "operational"},
    {"service_id": "SVC-003", "name": "Core Ledger", "department": "core_banking", "owner": "Carla Ibarra", "tier": "tier-1", "status": "operational"},
    {"service_id": "SVC-004", "name": "Identity Provider", "department": "security", "owner": "David Kim", "tier": "tier-1", "status": "operational"},
    {"service_id": "SVC-005", "name": "Data Warehouse Pipeline", "department": "data_platform", "owner": "Elena Petrova", "tier": "tier-2", "status": "operational"},
    {"service_id": "SVC-006", "name": "Mobile Banking App Backend", "department": "retail_banking", "owner": "Grace Lin", "tier": "tier-1", "status": "operational"},
    {"service_id": "SVC-007", "name": "Fraud Detection Engine", "department": "security", "owner": "Tom Walsh", "tier": "tier-2", "status": "operational"},
    {"service_id": "SVC-008", "name": "Loan Origination Portal", "department": "product", "owner": "Farid Haidari", "tier": "tier-2", "status": "operational"},
]

# Static copy mirroring docs/manifest.json's incident entries. Kept here as a
# standalone dataset (this service has no filesystem access to docs/) so tool
# results stay cross-referenceable with the incident report PDFs indexed in
# Pinecone, without coupling the two services at runtime.
INCIDENT_RECORDS = [
    {
        "incident_id": "INC-2025-08-14-001",
        "title": "Payment Gateway Timeout Outage - Card Present Transactions",
        "department": "payments",
        "severity": "high",
        "status": "resolved",
        "date": "2025-08-14",
    },
    {
        "incident_id": "INC-2025-10-02-002",
        "title": "Card Authorization Service Outage - Database Failover Delay",
        "department": "payments",
        "severity": "critical",
        "status": "resolved",
        "date": "2025-10-02",
    },
    {
        "incident_id": "INC-2025-12-19-003",
        "title": "ACH Batch Payment Processing Failure - Year-End Volume Spike",
        "department": "payments",
        "severity": "high",
        "status": "resolved",
        "date": "2025-12-19",
    },
    {
        "incident_id": "INC-2026-02-27-004",
        "title": "Duplicate Wire Transfer Submissions Due to Client Retry Storm",
        "department": "payments",
        "severity": "critical",
        "status": "resolved",
        "date": "2026-02-27",
    },
    {
        "incident_id": "INC-2026-05-11-005",
        "title": "Payment Gateway Timeout Recurrence - CNA Connection Pool",
        "department": "payments",
        "severity": "high",
        "status": "resolved",
        "date": "2026-05-11",
    },
    {
        "incident_id": "INC-2026-07-08-006",
        "title": "Mobile Banking App Login Outage - Identity Provider Certificate Expiry",
        "department": "retail_banking",
        "severity": "high",
        "status": "resolved",
        "date": "2026-07-08",
    },
]


def _matches(record: dict, query: str, department: str | None, fields: tuple[str, ...]) -> bool:
    if department and record.get("department") != department:
        return False
    if not query:
        return True
    needle = query.lower()
    return any(needle in str(record.get(field, "")).lower() for field in fields)


@mcp_server.tool()
def search_employee_directory(query: str = "", department: str | None = None) -> list[dict]:
    """Search the employee directory by name, title, or email substring, optionally filtered by department."""
    return [employee for employee in EMPLOYEES if _matches(employee, query, department, ("name", "title", "email"))]


@mcp_server.tool()
def search_service_catalog(query: str = "", department: str | None = None) -> list[dict]:
    """Search the service catalog by service name or owner, optionally filtered by department."""
    return [service for service in SERVICE_CATALOG if _matches(service, query, department, ("name", "owner"))]


@mcp_server.tool()
def search_incident_records(query: str = "", department: str | None = None) -> list[dict]:
    """Search incident records by title or incident id, optionally filtered by department."""
    return [
        incident
        for incident in INCIDENT_RECORDS
        if _matches(incident, query, department, ("title", "incident_id"))
    ]


if __name__ == "__main__":
    mcp_server.run(transport="streamable-http", host="0.0.0.0", port=9000)
