#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=/dev/null
source .env
uv run python image_gen_pipeline.py \
  --env-file .env \
  --prompt "${1:-A cute futuristic robot mascot, clean background, soft lighting, highly detailed}" \
  --model "${IMAGE_GEN_DEFAULT_MODEL:-gemini-3.1-flash-image-preview}" \
  --size "${IMAGE_GEN_DEFAULT_SIZE:-1792x1024}" \
  --n 1
