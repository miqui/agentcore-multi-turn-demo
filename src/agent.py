"""AgentCore HTTP entrypoint for the multi-turn session demo.

This module wires the pure logic in session_logic.py to the actual
Strands agent + bedrock-agentcore runtime. It is intentionally NOT
imported by the offline test suite (tests only import session_logic),
so it can freely depend on the strands-agents / bedrock-agentcore-sdk
packages that may not be installed in this local dev environment.

Deploying / invoking this via the AgentCore CLI is explicitly out of
scope for this scaffolding pass -- see README.md.
"""
from __future__ import annotations

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

from session_logic import SessionStore, parse_invocation_payload

app = BedrockAgentCoreApp()
_store = SessionStore()

# A minimal Strands agent. Multi-turn continuity for the *conversation*
# itself is handled by AgentCore Runtime's session routing (same
# runtimeSessionId -> same execution environment, 15-min idle / 8-hr
# max lifetime); this demo additionally tracks turn counts explicitly
# via SessionStore so the persistence is visible in the response.
agent = Agent()


@app.entrypoint
def invoke(payload: dict) -> dict:
    session_id, message = parse_invocation_payload(payload)

    result = agent(message)

    turn_info = _store.handle_turn(session_id, message)
    turn_info["agent_response"] = str(result)
    return turn_info


if __name__ == "__main__":
    app.run()
