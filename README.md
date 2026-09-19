# AgentCore Multi-Turn Session Demo

A minimal hello-world-style demo for AWS Bedrock AgentCore Runtime showing
**session context persistence across invocations** via a shared
`runtimeSessionId`.

## What this demonstrates

AgentCore Runtime routes repeated calls that share the same
`runtimeSessionId` to the same execution environment/session, which stays
alive for up to **15 minutes idle** / **8 hours total lifetime**. This demo
agent is "echo-ish": each turn echoes the input message back along with a
running turn counter and history for that session, so you can see state
persist across separate `invoke` calls as long as they reuse the same
session id.

## Layout

- `src/session_logic.py` — pure, stdlib-only session/turn tracking logic
  (no AWS/SDK imports). This is what the offline tests exercise.
- `src/agent.py` — the actual AgentCore entrypoint: a Strands `Agent`
  wrapped by `BedrockAgentCoreApp`, using `session_logic` for turn
  tracking. Requires `bedrock-agentcore` + `strands-agents` to import;
  not exercised by the local test suite.
- `tests/test_session_logic.py` — stdlib `unittest` suite for
  `session_logic.py`, fully offline.
- `requirements.txt` / `requirements-dev.txt` — runtime and dev deps.
- `Dockerfile` — AgentCore Runtime container contract (multi-stage build,
  non-root user, `EXPOSE 8080`, `CMD ["python", "src/agent.py"]`).
- `.github/workflows/ci.yml` — CI: ruff lint + unittest, no AWS calls.

## Running locally (offline, no AWS needed)

```bash
python -m unittest discover -s tests -v
ruff check .   # if ruff is installed
```

## Deploying (NOT done by this scaffold)

Deployment requires AWS credentials and the `agentcore` CLI /
`bedrock-agentcore-starter-toolkit`, e.g. roughly:

`agentcore launch` builds and pushes the image defined by the `Dockerfile`
in this repo (ARM64 by default) before deploying it to AgentCore Runtime.

```bash
pip install -r requirements.txt
agentcore configure --entrypoint src/agent.py
agentcore launch
agentcore invoke '{"prompt": "hi", "session_id": "demo-session-1"}'
agentcore invoke '{"prompt": "hi again", "session_id": "demo-session-1"}'
```

Calling `invoke` twice with the **same** `session_id` should show the turn
counter incrementing and history accumulating; a **different** `session_id`
starts a fresh count. These deploy/invoke steps are intentionally not run
as part of this scaffolding pass.
