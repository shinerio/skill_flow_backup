# Provider Notes

## APIMart image generation

Known documented endpoints:
- `POST https://api.apimart.ai/v1/images/generations`
- `GET https://api.apimart.ai/v1/tasks/{task_id}`
- `POST https://api.apimart.ai/v1/uploads/images`

Known model families exposed in docs navigation:
- Gemini 2.5 Flash Image preview (Nano banana)
- Gemini 3 Pro Image preview (Nano banana Pro)
- Gemini 3.1 Flash Image preview (Nano banana2)
- GPT-4o-image
- GPT-Image 1 / 1.5
- Seedream 4.0 / 4.5 / 5.0-Lite
- Flux Kontext
- Flux 2.0
- Qwen Image 2.0
- Z-Image-Turbo
- Grok Imagine 1.0

## Pipeline assumption

Most image tasks appear to be asynchronous:
1. submit generation
2. receive task identifier
3. poll task status
4. obtain result URL(s)
5. download result if needed
6. upload to final object storage target

## Storage target notes

Preferred naming clarity:
- Alibaba Cloud = OSS
- Huawei Cloud = OBS

If the environment says "Aliyun OBS", interpret it as one of these only after confirming the actual endpoint and credential format.

For implementation, prefer a generic object-storage abstraction with configurable:
- endpoint
- region
- bucket
- access key
- secret key
- public base URL or signed URL behavior
