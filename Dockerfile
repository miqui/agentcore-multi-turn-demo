# AgentCore Runtime container contract:
# - EXPOSE 8080, serve /invocations and /ping (handled by BedrockAgentCoreApp.run())
# - Non-root user
# - `agentcore launch` builds and pushes this image for ARM64 by default (Graviton),
#   so build locally with `docker build --platform linux/arm64 -t <tag> .` if testing
#   on an x86_64 host to match the deployed architecture.

# ---- builder stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY src/ ./src/

USER app

EXPOSE 8080

CMD ["python", "src/agent.py"]
