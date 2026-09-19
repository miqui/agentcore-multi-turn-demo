"""Pure, dependency-free session/turn tracking logic for the AgentCore
multi-turn session demo.

This module intentionally avoids importing any SDK (bedrock-agentcore,
strands, boto3, etc.) so it can be unit tested completely offline.
The AgentCore HTTP entrypoint (see agent.py) imports this module and
wraps it with the actual request/response handling and SDK calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionState:
    """In-memory state tracked for a single runtimeSessionId."""

    session_id: str
    turn_count: int = 0
    history: list[str] = field(default_factory=list)

    def record_turn(self, message: str) -> SessionState:
        """Record one turn of conversation and bump the counter."""
        self.turn_count += 1
        self.history.append(message)
        return self


class SessionStore:
    """A minimal in-process store keyed by runtimeSessionId.

    In the real AgentCore deployment, session continuity across
    invocations is provided by the AgentCore Runtime itself (same
    runtimeSessionId routes to the same execution environment, with an
    idle timeout of 15 minutes and a hard lifetime of 8 hours). This
    store exists purely to make that behavior demonstrable and testable
    within a single process/test run.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def handle_turn(self, session_id: str, message: str) -> dict:
        """Process one turn for a session and return a response payload.

        Returns a plain dict (JSON-serializable) describing the turn,
        echoing the message back along with session metadata -- this is
        the "echo-ish" behavior referenced in the demo name.
        """
        if not session_id:
            raise ValueError("session_id must be a non-empty string")
        if message is None:
            raise ValueError("message must not be None")

        state = self.get_or_create(session_id)
        state.record_turn(message)

        return {
            "session_id": state.session_id,
            "turn_count": state.turn_count,
            "echo": message,
            "history": list(state.history),
        }

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._sessions)


def parse_invocation_payload(payload: dict) -> tuple[str, str]:
    """Extract (session_id, message) from a raw invocation payload.

    Pure parsing logic, kept separate from any HTTP/SDK framework so it
    can be tested offline. Expected shape (mirrors a typical AgentCore
    /invocations body):

        {"prompt": "hello", "session_id": "abc-123"}

    "input" is also accepted as an alias for "prompt" for flexibility.
    """
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict")

    message = payload.get("prompt", payload.get("input"))
    if message is None:
        raise ValueError("payload must contain 'prompt' or 'input'")

    session_id = payload.get("session_id") or payload.get("runtimeSessionId")
    if not session_id:
        raise ValueError("payload must contain 'session_id' or 'runtimeSessionId'")

    return str(session_id), str(message)
