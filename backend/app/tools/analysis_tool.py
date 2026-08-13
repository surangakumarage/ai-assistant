from langchain_core.tools import tool

MAX_RECORDS = 500


@tool
async def analyze_records(records: list[dict], group_by: str) -> dict:
    """Perform structured analysis on a list of retrieved records (e.g. incident
    records or document chunks) by counting how many share each value of
    `group_by` (e.g. 'department', 'severity', 'status', 'document_type').
    Use this to summarize or find recurring patterns instead of eyeballing
    raw records one by one."""
    records = records[:MAX_RECORDS]
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get(group_by, "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return {"group_by": group_by, "counts": counts, "total_records": len(records)}
