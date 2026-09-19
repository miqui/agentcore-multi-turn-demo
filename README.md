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

## Architecture

- AgentCore Runtime (HTTP protocol) hosts the container image built from
  this repo's `Dockerfile`; each invocation hits `/invocations` on port 8080.
- Same `runtimeSessionId` → routed to the same isolated microVM session
  (15-min idle / 8-hr lifetime); in-process `SessionStore` keeps per-session
  turn count + history, making the persistence observable in the response.
- Inbound auth is IAM SigV4 (default) — no secrets in code.

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

## Run manually

### 1. Offline tests + lint (verified ✓ — no AWS needed)

```bash
cd ~/development/agentcore-multi-turn-demo
python3 -m unittest discover -s tests -v
uvx ruff check .
```

Expected output: `Ran 12 tests in 0.000s` → `OK`, then
`All checks passed!`

### 2. Deploy to AgentCore Runtime (⏳ pending — requires AWS CLI on host)

```bash
pip install -r requirements.txt
agentcore configure --entrypoint src/agent.py
agentcore launch
```

Expected: `agentcore launch` builds the Dockerfile image (ARM64 by
default), pushes it to ECR, and creates the AgentCore Runtime endpoint,
printing an agent ARN. Not yet run — flagged as the deploy pause point.

### 3. Exercise multi-turn persistence (⏳ pending — same pause point)

```bash
agentcore invoke '{"prompt": "hi", "session_id": "demo-session-1"}'
agentcore invoke '{"prompt": "hi again", "session_id": "demo-session-1"}'
agentcore invoke '{"prompt": "fresh start", "session_id": "demo-session-2"}'
```

Expected: first two calls share `demo-session-1` → `turn_count` goes
`1` → `2` and `history` accumulates; `demo-session-2` starts back at
`turn_count: 1` with its own history.
