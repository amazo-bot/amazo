# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.13-slim

# ── System deps ───────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Create a non-root user ─────────────────────────────────────────────────────
# The agent runs as `agent` — it cannot write outside /workspace
RUN useradd --create-home --shell /bin/bash agent

# ── Install uv globally (fast Python package manager) ─────────────────────────
RUN pip install --no-cache-dir uv

# ── Workspace ─────────────────────────────────────────────────────────────────
# /workspace is the volume mount point — all persistent changes live here.
# The container itself is ephemeral; only /workspace survives restarts.
WORKDIR /workspace

# ── Give the agent user ownership of the workspace ────────────────────────────
RUN chown agent:agent /workspace

# ── Switch to non-root ────────────────────────────────────────────────────────
USER agent

# ── Expose the uvicorn port ───────────────────────────────────────────────────
EXPOSE 8000

# ── Entrypoint ────────────────────────────────────────────────────────────────
# - Creates a venv if one doesn't exist yet (persisted in the volume)
# - Syncs dependencies from pyproject.toml
# - Starts uvicorn with --reload so file edits made by the agent take effect
#   immediately in the next chat message
CMD ["bash", "-c", "\
    if [ ! -d .venv ]; then \
    python -m venv .venv; \
    fi && \
    source .venv/bin/activate && \
    pip install --quiet --upgrade pip && \
    pip install --quiet uv && \
    uv sync && \
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload \
    "]