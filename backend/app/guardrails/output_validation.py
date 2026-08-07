import re

MAX_ANSWER_LENGTH = 4000

FALLBACK_ANSWER = "I'm not able to provide a reliable answer to that right now."

# Last-line defense against data exfiltration: if a compromised/injected
# context somehow got the model to echo something secret-shaped, redact it
# before it ever reaches the user rather than trusting the prompt alone.
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),  # OpenAI-style keys
    re.compile(r"pcsk_[A-Za-z0-9_-]{20,}"),  # Pinecone-style keys
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
]


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def validate_answer(answer: str) -> str:
    cleaned = (answer or "").strip()
    if not cleaned:
        return FALLBACK_ANSWER
    if len(cleaned) > MAX_ANSWER_LENGTH:
        cleaned = cleaned[:MAX_ANSWER_LENGTH].rstrip() + "…"
    return redact_secrets(cleaned)
