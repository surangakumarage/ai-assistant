import re

# Heuristic cues that retrieved/untrusted text is trying to override
# instructions rather than just being document content. Not a hard block -
# flagged chunks still pass through (a security runbook discussing this exact
# attack would legitimately contain these phrases), but they're marked so the
# model is put on notice and evaluators can see the guardrail firing.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|the) (previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"disregard (all|any|the) (previous|prior|above)", re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\byou are now\b", re.IGNORECASE),
    re.compile(r"\bnew instructions\s*:", re.IGNORECASE),
    re.compile(r"reveal (your|the) (instructions|prompt|api[_ ]?key)", re.IGNORECASE),
]


def scan_for_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def wrap_untrusted(source_id: str, title: str, text: str) -> str:
    """Delimit a piece of retrieved content as untrusted data, distinct from
    instructions. Explicit delimiting is the single most effective practical
    mitigation for indirect prompt injection - it stops the model from
    conflating "data to read" with "commands to follow"."""
    warning = " flagged=\"instruction-like-phrasing\"" if scan_for_injection(text) else ""
    return f'<untrusted_source id="{source_id}" title="{title}"{warning}>\n{text}\n</untrusted_source>'
