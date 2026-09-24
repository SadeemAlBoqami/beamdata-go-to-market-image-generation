#!/usr/bin/env bash
set -euo pipefail

BASE_MODEL="${BASE_MODEL:-black-forest-labs/FLUX.2-klein-4B}"
GGUF_MODEL="${GGUF_MODEL:-/models/flux-2-klein-4b-Q4_K_M.gguf}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
API_TOKEN="${API_TOKEN:?API_TOKEN is required}"

exec vllm serve "$BASE_MODEL" \
  --omni \
  --diffusion-quantization-config \
  "{\"method\":\"gguf\",\"gguf_model\":\"${GGUF_MODEL}\"}" \
  --host "$HOST" \
  --port "$PORT" \
  --api-key "$API_TOKEN"
