---
name: image-gen-pipeline
description: 端到端图片生成流水线：自动 prompt 编排 → APIMart 生成 → 阿里云 OSS 上传 → 返回可分享链接。内置信息图提示词编排能力。用户要生成图片、插画、海报、封面、信息图、概念图、头像并需要可分享链接时使用。
---

# 图片生成流水线

## 何时使用

**触发条件：**
- 用户明确要求生成图片/插画/海报/封面/信息图/头像，并需要一个可分享的链接
- 用户希望先优化 prompt 再生成，不是直接把原话扔给模型
- 需要将生成结果托管在你自己的阿里云 OSS 上，而非平台自有存储
- **特别支持**：生成专业信息图（infographic），内置布局×风格提示词编排能力

**不触发条件：**
- 用户只是问“什么是图片生成”，不要求真生成
- 已经有图片文件，只需要上传，不需要生成

## 核心规则

1. **职责分离**：本技能内置的提示词编排能力用于信息图生成；其他类型图片 LLM 自主选择已有合适技能编写高质量 prompt，本技能只负责编排和执行
2. **异步生成**：适配 APIMart 异步任务模型，自动轮询直到完成
3. **配置安全**：所有密钥从 `.env` 读取，永远不暴露在对话中
4. **输出规范**：最终返回阿里云 OSS 公开链接，可直接用于文章、分享、嵌入

## 信息图生成

当用户要求生成"信息图"、"infographic"、"可视化"、"高密度信息大图"时，**直接使用本技能内置的提示词编排能力**：

### 布局选项（21种）

| Layout | Best For |
|--------|----------|
| `linear-progression` | 时间线、流程、教程 |
| `binary-comparison` | A vs B、前后对比、优缺点 |
| `comparison-matrix` | 多因素比较 |
| `hierarchical-layers` | 金字塔、优先级层级 |
| `tree-branching` | 分类、分类法 |
| `hub-spoke` | 核心概念+相关项 |
| `structural-breakdown` | 分解图、横截面 |
| `bento-grid` | 多个主题、概览（默认） |
| `iceberg` | 表面 vs 隐藏方面 |
| `bridge` | 问题-解决方案 |
| `funnel` | 转化、筛选 |
| `isometric-map` | 空间关系 |
| `dashboard` | 指标、KPIs |
| `periodic-table` | 分类集合 |
| `comic-strip` | 叙述、序列 |
| `story-mountain` | 情节结构、张力弧 |
| `jigsaw` | 相互关联的部分 |
| `venn-diagram` | 重叠概念 |
| `winding-roadmap` | 旅程、里程碑 |
| `circular-flow` | 循环、重复流程 |
| `dense-modules` | 高密度模块、数据丰富指南 |

### 风格选项（20种）

| Style | Description |
|-------|-------------|
| `craft-handmade` | 手绘、纸艺（默认） |
| `claymation` | 3D 粘土人偶、定格动画 |
| `kawaii` | 日式可爱、马卡龙色系 |
| `storybook-watercolor` | 柔和水彩、 whimsical |
| `chalkboard` | 黑板粉笔 |
| `cyberpunk-neon` | 霓虹发光、未来感 |
| `bold-graphic` | 漫画风格、半色调 |
| `aged-academia` | 复古科学、棕褐色 |
| `corporate-memphis` | 扁平矢量、充满活力 |
| `technical-schematic` | 蓝图、工程制图 |
| `origami` | 折纸、几何 |
| `pixel-art` | 复古 8-bit |
| `ui-wireframe` | 灰度线框原型 |
| `subway-map` | 交通图 |
| `ikea-manual` | 极简线条 |
| `knolling` | 整齐平铺 |
| `lego-brick` | 乐高积木 |
| `pop-laboratory` | 蓝图网格、坐标标记、实验室精度 |
| `morandi-journal` | 手绘涂鸦、莫兰迪暖色调 |
| `retro-pop-grid` | 70年代复古波普、瑞士网格、粗轮廓 |

### 推荐组合

| 内容类型 | 布局 + 风格 |
|----------|-------------|
| 时间线/历史 | `linear-progression` + `craft-handmade` |
| 分步教程 | `linear-progression` + `ikea-manual` |
| A vs B 对比 | `binary-comparison` + `corporate-memphis` |
| 层级结构 | `hierarchical-layers` + `craft-handmade` |
| 重叠概念 | `venn-diagram` + `craft-handmade` |
| 转化漏斗 | `funnel` + `corporate-memphis` |
| 循环流程 | `circular-flow` + `craft-handmade` |
| 技术分解 | `structural-breakdown` + `technical-schematic` |
| 数据指标 | `dashboard` + `corporate-memphis` |
| 教育内容 | `bento-grid` + `chalkboard` |
| 旅程规划 | `winding-roadmap` + `storybook-watercolor` |
| 分类整理 | `periodic-table` + `bold-graphic` |
| 产品指南 | `dense-modules` + `morandi-journal` |
| 技术指南 | `dense-modules` + `pop-laboratory` |
| 潮流指南 | `dense-modules` + `retro-pop-grid` |

默认：`bento-grid` + `craft-handmade`

### 关键字快捷方式

| 用户关键字 | 自动布局 | 推荐风格 | 默认比例 |
|------------|----------|----------|----------|
| 高密度信息大图 / high-density-info | `dense-modules` | `morandi-journal`, `pop-laboratory`, `retro-pop-grid` | portrait |
| 信息图 / infographic | `bento-grid` | `craft-handmade` | landscape |

### 信息图工作流

1. **分析内容**：分析主题、数据结构、复杂度、色调、受众
2. **推荐组合**：根据内容推荐 3-5 个布局×风格组合（关键字匹配直接选中）
3. **确认选项**：确认组合、宽高比、语言
4. **生成提示词**：拼接布局定义 + 风格定义 + 基础模板 + 结构化内容 → 生成最终 prompt
5. **执行生成**：调用 APIMart 生成 → 上传 OSS → 返回链接

完整定义参考：`references/layouts/` 和 `references/styles/`

## 必做步骤

1. **明确需求**：确认图片类型、风格、尺寸/比例
2. **生成 prompt**：
   - **如果是信息图** → 使用本技能内置的能力编排提示词
   - **如果有其他匹配的 prompt 写作技能** → 加载它生成最终 prompt
   - **如果都没有** → 直接按结构化原则编写 prompt
3. **执行生成**：调用 `scripts/image_gen_pipeline.py`，传入 prompt、模型、尺寸
4. **返回结果**：输出 OSS 链接 + 一句话说明

## 配置依赖

- 依赖：`requests python-dotenv oss2`（已预装在 `scripts/.venv`）
- 配置：`scripts/.env` 中填写 `APIMART_API_KEY` + 阿里云 OSS 信息（已有模板 `.env.example`）
- 执行：从 `scripts/` 目录运行，保证 `.env` 能被正确读取

## 输出结果

最终给用户返回：
- 生成好的图片 OSS 链接
- 一句话描述生成内容（含布局+风格）
- 使用的模型

不要输出原始 JSON、轮询日志、调试信息。
