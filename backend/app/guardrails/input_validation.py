from functools import lru_cache

from app.retrieval.loader import load_manifest

MAX_QUESTION_LENGTH = 2000


class InvalidRequestError(ValueError):
    pass


@lru_cache
def known_departments() -> frozenset[str]:
    return frozenset(entry["department"] for entry in load_manifest())


def validate_question(question: str) -> str:
    cleaned = (question or "").strip()
    if not cleaned:
        raise InvalidRequestError("Question must not be empty.")
    if len(cleaned) > MAX_QUESTION_LENGTH:
        raise InvalidRequestError(f"Question exceeds the {MAX_QUESTION_LENGTH} character limit.")
    return cleaned


def validate_department(department: str | None) -> str | None:
    if not department:
        return None
    if department not in known_departments():
        raise InvalidRequestError(f"Unknown department '{department}'.")
    return department


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def truncate(text: str, max_length: int) -> str:
    return text[:max_length] if text else text
