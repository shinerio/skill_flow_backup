# Aliyun OSS Configuration

Use `.env` for all sensitive values.

Required environment variables:

```env
APIMART_API_KEY=...
ALIYUN_OSS_ACCESS_KEY_ID=...
ALIYUN_OSS_ACCESS_KEY_SECRET=...
ALIYUN_OSS_BUCKET=...
ALIYUN_OSS_REGION=cn-hangzhou
```

Optional environment variables:

```env
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_PUBLIC_BASE_URL=https://<bucket>.<region-endpoint>
ALIYUN_OSS_PREFIX=generated-images/
IMAGE_GEN_DEFAULT_MODEL=gemini-3.1-flash-image-preview
IMAGE_GEN_DEFAULT_SIZE=1536x1024
IMAGE_GEN_DOWNLOAD_DIR=/tmp/openclaw-image-gen
```

Notes:
- If `ALIYUN_OSS_ENDPOINT` is omitted, derive it from region as `https://oss-${ALIYUN_OSS_REGION}.aliyuncs.com`.
- If `ALIYUN_OSS_PUBLIC_BASE_URL` is omitted, construct a virtual-hosted-style URL when possible.
- Keep `.env` outside chat output. Never print secrets.
- Uploaded object keys should default to: `generated-images/YYYY/MM/DD/<slug>-<timestamp>.png`
