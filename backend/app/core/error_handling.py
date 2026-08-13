import asyncio

import httpx
from ollama import ResponseError as OllamaResponseError
from openai import APIError as OpenAIAPIError
from pinecone.exceptions import PineconeException

# Ordered most-specific-first; the first matching type wins. Maps the
# assignment's Error Handling categories (LLM / vector DB / MCP / tool
# timeout failures) to a message safe to show a user - no stack traces or
# internal details leak through.
_ERROR_MESSAGES: list[tuple[type[BaseException], str]] = [
    (OllamaResponseError, "The language model provider is currently unavailable. Please try again shortly."),
    (OpenAIAPIError, "The embedding service is currently unavailable, so search can't run right now. Please try again shortly."),
    (PineconeException, "The document search index is currently unavailable. Please try again shortly."),
    (asyncio.TimeoutError, "The request took too long and timed out. Please try again."),
    (httpx.HTTPError, "A downstream service (e.g. MCP) is currently unavailable. Please try again shortly."),
]


def friendly_error(exc: BaseException) -> str:
    for exc_type, message in _ERROR_MESSAGES:
        if isinstance(exc, exc_type):
            return message
    return "Something went wrong while processing your request. Please try again shortly."
