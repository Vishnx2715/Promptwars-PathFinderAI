#!/usr/bin/env bash
set -e

# Run database seeds if database doesn't exist
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
