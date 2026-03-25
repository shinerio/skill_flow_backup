---
name: auto-codehub-review
description: 自动review CodeHub PR/MR并将review意见提交到平台。当用户提到"自动review"、"codehub review"、"pr review"、"mr review"、"review代码"、"提交review意见"或提供CodeHub PR/MR URL时，必须使用此skill。支持自动克隆代码仓、切换分支、加载上下文、调用code-reviewer进行代码检视，并将review意见批量提交到CodeHub平台。
---

# Auto CodeHub Review

自动review CodeHub上的PR/MR并将review意见提交到平台。

## 使用场景

当用户提供CodeHub PR/MR URL（如 `https://codehub-g.huawei.com/cis/nsd/common/quark-frameworks/merge_requests/2127`）或明确表示需要对CodeHub上的代码进行自动化review时，使用此skill。

## 执行流程

### 1. 解析PR URL

从用户提供的URL中提取：
- **项目路径**: URL中域名后的路径部分（如 `cis/nsd/common/quark-frameworks`）
- **MR编号**: merge_requests/后的数字（如 `2127`）
- **仓库名称**: 项目路径的最后一部分（如 `quark-frameworks`）

示例解析：
```
URL: https://codehub-g.huawei.com/cis/nsd/common/quark-frameworks/merge_requests/2127
项目路径: cis/nsd/common/quark-frameworks
MR编号: 2127
仓库名称: quark-frameworks
```

### 2. 代码仓准备

检查当前目录下是否存在该代码仓：
- 如果存在：跳过克隆步骤
- 如果不存在：执行 `git clone ssh://git@codehub-dg-g.huawei.com:2222/<项目路径>.git`

**注意**: 使用SSH协议，CodeHub的git clone URL格式为 `git clone ssh://git@codehub-dg-g.huawei.com:2222/<项目路径>.git`

### 3. 获取MR信息

使用CodeHub API获取MR详细信息：
- 调用 `get_project` 获取项目ID
- 调用 `get_merge_request_changes` 获取MR的变更内容和source_branch信息

### 4. 分支切换

进入代码仓目录后执行：
1. `git fetch --all` - 拉取所有远端分支
2. `git reset --hard origin/<source_branch>` - 强制切换到PR分支的最新提交

**为什么使用 reset --hard**:
- 确保本地代码与远端PR分支完全一致
- 避免本地未提交的更改影响review结果
- 保证review的是最新代码

### 5. 加载上下文

加载项目的上下文信息以提供更准确的review：
- 检查并加载仓库根目录的 `AGENTS.md` 文件（如果存在）
- 检查并加载 `.relay/RELAY_SKILLS.md` 文件（如果存在）
- 这些文件包含项目特定的编码规范、架构信息、review关注点等

### 6. 代码Review

调用 `code-reviewer` skill对当前PR进行review：
- 将代码仓目录设置为review根目录
- 将MR的变更内容传递给code-reviewer
- code-reviewer会分析代码变更并生成review意见

**传递给code-reviewer的信息**:
- 项目路径和MR编号
- 变更的文件列表
- 每个文件的具体diff内容
- 加载的上下文信息（AGENTS.md等）

### 7. 提交Review意见

解析code-reviewer的输出，提取review意见并提交到CodeHub：

**Review意见格式识别**:
code-reviewer应该输出结构化的review意见，每条意见包含：
- **文件路径**: 被review的文件
- **行号**: 问题所在的行号
- **严重级别**: `error`（错误）、`warning`（警告）、`suggestion`（建议）
- **描述**: 问题的详细说明

**批量提交**:
- 对每条review意见调用 `create_merge_request_review` API
- 参数包括：
  - `project_id`: 项目ID
  - `merge_request_iid`: MR编号
  - `body`: review意见内容
  - `severity`: 严重级别（默认 `suggestion`）
  - `need_to_resolve`: 是否需要解决（默认 `true`）

### 8. 输出执行结果

以清晰的格式输出执行结果：

```markdown
## CodeHub Auto Review 执行结果

### 基本信息
- 项目: cis/nsd/common/quark-frameworks
- MR编号: 2127
- MR链接: https://codehub-g.huawei.com/cis/nsd/common/quark-frameworks/merge_requests/2127

### 执行步骤
✅ 步骤1: 解析PR URL
✅ 步骤2: 代码仓准备
✅ 步骤3: 获取MR信息
✅ 步骤4: 分支切换
✅ 步骤5: 加载上下文
✅ 步骤6: 代码Review
✅ 步骤7: 提交Review意见

### Review意见摘要
- 总计: 5条意见
- Error: 1条
- Warning: 2条
- Suggestion: 2条

### 提交结果
✅ 成功提交: 5/5条review意见

### 查看详情
请访问MR链接查看详细review意见: https://codehub-g.huawei.com/cis/nsd/common/quark-frameworks/merge_requests/2127
```

## 错误处理

### URL解析失败
- 检查URL格式是否正确
- 确认URL包含 `merge_requests/` 部分

### Git操作失败
- 检查网络连接
- 确认Git凭证配置正确
- 检查磁盘空间

### CodeHub API调用失败
- 检查API访问权限
- 确认MR编号正确
- 检查网络连接

### code-reviewer调用失败
- 确认code-reviewer skill已安装
- 检查code-reviewer的输出格式

### Review意见提交失败
- 记录失败的意见内容
- 继续提交其他意见
- 在最终结果中报告失败数量

## 重试机制

对于可重试的操作（如API调用、git操作），实现简单的重试机制：
- 最多重试3次
- 每次重试间隔2秒
- 记录重试次数和原因

## 工具使用

### CodeHub MCP工具
- `get_project`: 获取项目信息
- `get_merge_request_changes`: 获取MR变更内容
- `create_merge_request_review`: 提交review意见

### Git工具
- `git_init`: 初始化仓库（如需要）
- `git_checkout`: 切换分支
- `git_status`: 检查状态
- `git_log`: 查看提交历史

### 其他工具
- `execute_command`: 执行git命令（如 `git fetch`, `git reset`）
- `read`: 读取上下文文件（AGENTS.md等）
- `skill_play`: 调用code-reviewer skill

## 注意事项

1. **安全性**: 不要在review意见中泄露敏感信息
2. **准确性**: 确保review意见基于正确的代码版本
3. **友好性**: review意见应该建设性、具体、可操作
4. **性能**: 对于大型PR，考虑分批处理文件
5. **权限**: 确保有权限访问CodeHub项目和提交review

## 示例对话

**用户**: 自动review这个PR: https://codehub-g.huawei.com/cis/nsd/common/quark-frameworks/merge_requests/2127

**执行过程**:
1. 解析URL获取项目路径和MR编号
2. 检查并克隆代码仓（如需要）
3. 获取MR信息和变更内容
4. 切换到PR分支
5. 加载AGENTS.md等上下文文件
6. 调用code-reviewer进行review
7. 提交review意见到CodeHub
8. 输出执行结果

**输出**: 见"输出执行结果"部分的格式

## 与code-reviewer的协作

此skill负责：
- CodeHub集成（获取MR信息、提交review意见）
- 代码仓管理（克隆、切换分支）
- 上下文加载（AGENTS.md等）
- 流程编排和结果输出

code-reviewer skill负责：
- 实际的代码分析
- 生成review意见
- 提供改进建议

两者通过结构化的输出格式进行协作，确保review意见能够被正确提取和提交。