# 图片生成流水线（image-gen-pipeline）

APIMart 图片生成 + 阿里云 OSS 上传完整流水线。

让 OpenClaw 拥有：**prompt 编排 → APIMart 异步生成 → OSS 上传 → 返回可分享链接** 的完整端到端图片生成能力。

## 功能特点

- **职责分离**：prompt 编写由 LLM 自主选择已有技能完成，本技能只负责编排和执行
- **原生支持异步生成**：完美适配 APIMart 异步任务模型，自动轮询直到完成
- **像素尺寸自动转换**：支持输入 `1792x1024` 这种像素尺寸，自动转换成 APIMart 需要的 `宽高比 + 分辨率` 格式
- **敏感配置安全**：所有 API Key 和 OSS 凭证都从 `.env` 读取，不会出现在对话或版本控制中
- **多模型支持**：支持 APIMart 所有图片模型，包括：
  - Gemini 3.1 Flash Image Preview（Nano banana2）
  - Gemini 3 Pro Image Preview（Nano banana Pro）
  - Seedream 系列
  - Flux 系列
  - 通义千问图片生成系列
- **开箱即用**：依赖安装简单，配置清晰，一键运行

## 目录结构

```
image-gen-pipeline/
├── SKILL.md                      # OpenClaw 技能说明（供 OpenClaw 读取）
├── README.md                      # 这份文档
├── references/
│   ├── aliyun-oss-config.md       # 阿里云 OSS 配置约定
│   ├── invocation-contract.md    # 调用契约说明
│   ├── provider-notes.md         # APIMart 说明
│   └── usage.md                   # 使用说明
└── scripts/
    ├── .env.example              # 环境变量模板
    ├── image_gen_pipeline.py    # 主执行器
    ├── requirements.txt          # Python 依赖
    └── run-example.sh           # 快捷运行脚本
```

## 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/skills/image-gen-pipeline/scripts
uv venv
uv pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 APIMart API Key 和阿里云 OSS 信息
vim .env
```

必填配置：
```env
APIMART_API_KEY=你的APIMart_API_Key

# 阿里云 OSS
ALIYUN_OSS_ACCESS_KEY_ID=你的AccessKeyID
ALIYUN_OSS_ACCESS_KEY_SECRET=你的AccessKeySecret
ALIYUN_OSS_BUCKET=你的Bucket名称
ALIYUN_OSS_REGION=cn-beijing
```

可选配置：
```env
ALIYUN_OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com
ALIYUN_OSS_PUBLIC_BASE_URL=https://你的bucket.oss-cn-beijing.aliyuncs.com
ALIYUN_OSS_PREFIX=ai-generated/
IMAGE_GEN_DEFAULT_MODEL=gemini-3.1-flash-image-preview
IMAGE_GEN_DEFAULT_SIZE=16:9
IMAGE_GEN_DOWNLOAD_DIR=/tmp/openclaw-image-gen
IMAGE_GEN_POLL_INTERVAL_SECONDS=3
IMAGE_GEN_TIMEOUT_SECONDS=180
```

### 3. 测试运行

```bash
bash run-example.sh "一个可爱的未来机器人吉祥物，干净背景"
```

如果一切正常，你会得到类似输出：

```json
{
  "ok": true,
  "provider": "apimart",
  "model": "gemini-3.1-flash-image-preview",
  "task_id": "task_xxx",
  "prompt": "一个可爱的未来机器人吉祥物，干净背景",
  "local_files": [
    "/tmp/openclaw-image-gen/a-cute-futuristic-robot-mascot-clean-background-20260403-123456-1.jpg"
  ],
  "uploaded": [
    {
      "url": "https://你的bucket.oss-cn-beijing.aliyuncs.com/ai-generated/2026/04/03/xxx.jpg",
      "object_key": "ai-generated/2026/04/03/xxx.jpg",
      "content_type": "image/jpeg"
    }
  ]
}
```

## 工作流程

### OpenClaw 技能工作流

1. **理解需求**：分析用户的图片需求，提取主题、风格、尺寸等信息
2. **选择 prompt 编写方式**：让 LLM 自主判断是否需要加载已有技能来生成高质量 prompt，如果没有合适技能就自己写
3. **生成结构化参数**：产出最终 prompt + 推荐模型 + 推荐尺寸
4. **调用执行器**：执行 `image_gen_pipeline.py` 完成生成和上传
5. **返回结果**：把最终 OSS 链接和简要说明返回给用户

### 执行器工作流

1. **解析尺寸**：如果输入是像素格式（如 `1792x1024`），自动转换成 APIMart 需要的 `宽高比 + 分辨率`
   - 例如 `1792x1024` → `16:9` + `2K`
2. **提交生成任务**：调用 APIMart `POST /v1/images/generations`
3. **轮询任务状态**：每隔几秒调用 `GET /v1/tasks/{task_id}` 直到完成/失败/超时
4. **下载图片**：从 APIMart 返回的 URL 下载图片到本地临时目录
5. **上传 OSS**：把图片上传到阿里云 OSS，按 `{前缀}/{年}/{月}/{日}/{slug}-{时间戳}.扩展名` 路径存储
6. **返回结果**：输出 JSON，包含 `uploaded[0].url` 作为最终可分享链接

## 在 OpenClaw 对话中使用

用户只需要用自然语言提需求，例如：

- 帮我生成一张赛博朋克风格的 Telegram 频道封面
- 做一个极简风 AI 助手头像
- 给这篇教程生成一张原理示意图
- 生成一张 16:9 技术文章头图，主题是 XXX

`image-gen-pipeline` 技能会自动走完完整流程，最后返回 OSS 链接。

## 参数说明

### 支持的尺寸格式

APIMart 使用 `size`（比例） + `resolution`（精度）格式，本工具支持两种输入：

1. **直接使用 APIMart 格式**：
   - `size`：比例，如 `1:1`, `16:9`, `9:16`, `4:5`, `5:4`
   - 完整支持比例列表请参考 APIMart 官方文档

2. **像素格式**（推荐，自动转换）：
   - `1024x1024` → `1:1` + `1K`
   - `1792x1024` → `16:9` + `2K`
   - `1024x1792` → `9:16` + `2K`
   - 工具会自动计算最简比例，并根据最大边长选择精度

### 支持的模型

常用模型 ID：

| 模型 ID | 说明 |
|---------|------|
| `gemini-3.1-flash-image-preview` | Nano banana2，默认推荐 |
| `gemini-3-pro-image-preview` | Nano banana Pro，更高质量 |
| `seedream-4.5` | 字节跳动 Seedream 4.5 |
| `seedream-4.0` | 字节跳动 Seedream 4.0 |
| `flux-2.0` | FLUX 2.0 |
| `flux-kontext` | FLUX Kontext（图片编辑场景） |
| `qwen-image-2.0` | 通义千问图片生成 |

完整模型列表请参考 [APIMart 官方文档](https://docs.apimart.ai/)。

## 故障排查

### 错误：`unsupported aspect ratio`

- 原因：你输入的像素尺寸无法转换成合法比例，或者 APIMart 不支持该比例
- 解决：直接使用比例格式，比如 `16:9`

### 错误：`no task_id found in provider response`

- 原因：APIMart 响应结构变化，或者认证失败
- 解决：检查 `APIMART_API_KEY` 是否正确

### 错误：`AccessDenied` / 上传 OSS 失败

- 原因：OSS AccessKey 不对，或者 bucket 名称/region/endpoint 配置错误
- 解决：检查 `.env` 中的 OSS 配置，确认 endpoint 和 region 匹配

### 错误：`The bucket you are attempting to access must be addressed using the specified endpoint`

- 原因：endpoint 配置错误
- 解决：按照阿里云提示修改 `ALIYUN_OSS_ENDPOINT`

## 输出示例

成功输出：

```json
{
  "ok": true,
  "provider": "apimart",
  "model": "gemini-3.1-flash-image-preview",
  "task_id": "task_01KN9HCBTFQ4X95F5JJFPN0FER",
  "prompt": "A clean infographic diagram illustrating how Claude Code works with Java LSP...",
  "local_files": [
    "/tmp/openclaw-image-gen/xxx-20260403-112452-1.jpg"
  ],
  "uploaded": [
    {
      "url": "https://shinerio.oss-cn-beijing.aliyuncs.com/ai-generated/2026/04/03/xxx.jpg",
      "object_key": "ai-generated/2026/04/03/xxx.jpg",
      "content_type": "image/jpeg"
    }
  ]
}
```

失败输出：

```json
{
  "ok": false,
  "stage": "generate",
  "error": "provider returned 401",
  "body": "..."
}
```

`stage` 告诉你错误发生在哪个阶段：
- `config`: 配置缺失
- `generate`: 提交生成任务失败
- `poll`: 轮询任务失败/超时
- `download`: 下载图片失败
- `upload`: OSS 上传失败

## 作者

为 OpenClaw 打造，shinerio 定制。

## 许可证

MIT
