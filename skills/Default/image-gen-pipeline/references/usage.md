# Usage

## What this skill does

This skill orchestrates:
1. prompt authoring via the best existing suitable skill or direct LLM prompt writing
2. image generation via APIMart
3. upload to Aliyun OSS
4. returning the final hosted URL

## Setup

### 1. Create `.env`

In:

`skills/image-gen-pipeline/scripts/.env`

Start from:

`skills/image-gen-pipeline/scripts/.env.example`

### 2. Install dependencies

Preferred:

```bash
cd ~/.openclaw/workspace/skills/image-gen-pipeline/scripts
uv venv
uv pip install -r requirements.txt
```

## Manual executor test

```bash
cd ~/.openclaw/workspace/skills/image-gen-pipeline/scripts
uv run python image_gen_pipeline.py \
  --env-file .env \
  --prompt "A cute futuristic robot mascot, clean background, soft lighting, highly detailed" \
  --model "gemini-3.1-flash-image-preview" \
  --size "1536x1024" \
  --n 1
```

## Expected result

The script prints JSON. On success, use:
- `uploaded[0].url`

as the canonical result.

## Chat usage pattern

User examples that should trigger this skill:
- 生成一张赛博朋克频道封面图
- 做一个极简风 AI 头像
- 画一张适合 Telegram 公告的横图
- 帮我生成一张文章头图，然后给我可分享链接

## Skill behavior in chat

When triggered, the skill should:
1. understand the user’s visual intent
2. let the LLM decide whether an existing skill should be loaded for prompt authoring
3. produce the final prompt
4. call the executor script
5. return the uploaded OSS URL
