ACCESS_LEVELS = ["public", "internal", "confidential", "restricted"]


def _rank(level: str) -> int:
    try:
        return ACCESS_LEVELS.index(level)
    except ValueError:
        # Unknown levels are treated as the most restrictive rather than the
        # most permissive - fail closed on bad/missing metadata.
        return len(ACCESS_LEVELS)


def filter_by_access_level(items, max_access_level: str):
    """Drop any item whose `.access_level` exceeds `max_access_level`. Works on
    any object exposing that attribute (RetrievedChunk, etc.) - kept
    dependency-free of the retrieval layer's types."""
    ceiling = _rank(max_access_level)
    return [item for item in items if _rank(item.access_level) <= ceiling]
