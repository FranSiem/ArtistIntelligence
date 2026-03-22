#!/usr/bin/env bash
set -e

cleanup() {
  kill 0
}
trap cleanup EXIT

source .venv/bin/activate
.venv/bin/uvicorn app.main:app --port 8000 --workers 1 --reload &

cd frontend && npm run dev &

wait
