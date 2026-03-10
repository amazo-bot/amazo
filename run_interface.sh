#!/bin/bash

if [ ! -d ".venv" ]; then
    # create virtualenv
    python3 -m venv .venv
    conda deactivate 2>/dev/null || deactivate 2>/dev/null || true
    source .venv/bin/activate
    pip install --upgrade pip
    pip install uv
    uv sync
fi

conda deactivate 2>/dev/null || deactivate 2>/dev/null || true
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
