# Invocation Contract

## Prompt authoring stage

The LLM should first produce a structured result conceptually equivalent to:

```json
{
  "prompt": "final image prompt",
  "model": "optional recommended model",
  "size": "optional recommended size",
  "n": 1
}
```

If no model or size is specified, the executor defaults from `.env`.

## Executor invocation

Call:

```bash
uv run python image_gen_pipeline.py \
  --env-file .env \
  --prompt "<FINAL_PROMPT>" \
  --model "<MODEL_IF_ANY>" \
  --size "<SIZE_IF_ANY>" \
  --n 1
```

Run from:

```bash
~/.openclaw/workspace/skills/image-gen-pipeline/scripts
```

## Executor success result

```json
{
  "ok": true,
  "provider": "apimart",
  "model": "...",
  "task_id": "...",
  "prompt": "...",
  "local_files": ["..."],
  "uploaded": [
    {
      "url": "https://...",
      "object_key": "generated-images/...",
      "content_type": "image/png"
    }
  ]
}
```

## What the assistant should return to the user

Return a concise result:
- generation succeeded
- model used
- final OSS URL

Optionally include a one-line summary of the visual result.
