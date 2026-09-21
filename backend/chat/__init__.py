"""Ask KAVACH conversational chat (Gemini Interactions API)."""

from .gemini import generate_reply
from .session import append, get_history, new_conversation_id, reset

__all__ = ["generate_reply", "append", "get_history", "new_conversation_id", "reset"]
