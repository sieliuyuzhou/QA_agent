from .chat import ChatService
from .exceptions import (
    ModelException,
    ModelTimeoutError,
    ModelRateLimitError,
    ModelAuthenticationError,
    ModelConnectionError,
)

__all__ = [
    "ChatService",
    "ModelException",
    "ModelTimeoutError",
    "ModelRateLimitError",
    "ModelAuthenticationError",
    "ModelConnectionError",
]

_service_instance = None


def get_service() -> ChatService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ChatService()
    return _service_instance
