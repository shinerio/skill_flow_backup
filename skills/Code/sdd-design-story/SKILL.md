---
name: sdd-design-story
description: 帮助用户按照codespec的sdd规范完成story设计，输出或完善proposal/delta-spec/delta-design/tasks。支持多次重入场景，能够接续执行步骤和问答进度。负责生成文档，不执行代码开发工作。
---

# SDD Designer for Story

SDD 是 specification driven design，本 skill 能够在用户需要做 story 设计的时候，用引导和协作的方式，引导用户完成 proposal/delta-spec/delta-design 的设计，并完成 tasks 分解。为后续直接编码提供设计输出。
本 skill 的内容不包含编码。

## 工作流概览

```
需求澄清 → 增量规格 → 增量设计 → 任务规划 → 一致性验证
(proposal) (delta-spec) (delta-design) (tasks) (validation)
```

**每个步骤的标准流程**：
```
步骤 1-4：第一阶段：准备/收集 → 第二阶段：交互式澄清（必须执行）→ 第三阶段：生成文档 → 第四阶段：用户确认（必须执行）→ 第五阶段：校验（可选）
步骤 5：第一阶段：读取文档 → 第二阶段：AI 自主分析（必须执行）→ 第三阶段：生成验证报告 → 第四阶段：提供修订建议
```

**核心特性**：
- 🔄 支持从任意步骤开始或跳转
- 📝 提供标准化输出模板
- 💡 内置问答逻辑和渐进式知识
- ✅ 确保输出符合质量标准
- 🔍 验证文档链一致性
- 📍 支持多次重入和上下文恢复
- ⚠️ **强制执行**：每个步骤必须完成"交互式澄清"阶段后才能生成文档

**SDD 方法论背景**：详见 [references/sdd-methodology.md](references/sdd-methodology.md)

## 状态管理与重入机制

本 skill 使用状态机来追踪工作流进度和文档状态，确保工作流的可追溯性和可恢复性，同时支持多次重入场景。

### 状态定义

**当前状态结构**：详见 [templates/state.json](templates/state.json)

**状态说明**：
- `current_step`：当前所处的步骤
- `iteration`：当前迭代次数（用于追踪修订，每次修订 +1）
- `files`：各文档的状态信息
  - `status`：文档状态
    - `pending`：待生成
    - `in_progress`：生成中
    - `completed`：已完成
    - `modified`：已修订
  - `version`：文档版本号
- `last_action`：最后一次执行的操作
- `next_action`：建议的下一步操作
- `history`：操作历史记录

---

### 状态持久化

**存储位置**：`{项目根目录}/codespec/changes/{工作目录}/state.json`

**持久化时机**：
- 每个步骤完成后自动保存
- 每次修订后自动保存
- 每次跳转后自动保存
- 用户显式触发"保存状态"时保存

**时间戳更新规则**：
- 每次更新文档状态时，必须使用**当前实际时间**更新对应文件的 `last_modified` 字段
- 时间戳格式：ISO8601 格式（北京时间 UTC+8），例如：`2026-02-13T14:30:00+08:00`
- 获取当前时间的方法：
  - Windows: 使用 PowerShell 命令 `Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"`
  - Linux/Mac: 使用 `date +"%Y-%m-%dT%H:%M:%S%:z"`
- 更新 `history` 数组时，每条记录的 `timestamp` 字段也必须使用当前实际时间
- **禁止使用示例时间或硬编码时间**

**恢复机制**：
- 对话中断后，读取 state.json 恢复工作流状态
- 展示当前进度和下一步操作
- 允许用户从任意步骤继续

---

### 通用状态更新规范

**适用场景**：每个步骤完成文档生成后，必须按照以下规范更新 state.json

**更新步骤**：

1. **获取当前时间戳**
   - Windows (PowerShell):
     ```powershell
     Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
     # 输出示例：2026-02-13T14:30:00+08:00
     ```
   - Linux/Mac:
     ```bash
     date +"%Y-%m-%dT%H:%M:%S%:z"
     # 输出示例：2026-02-13T14:30:00+08:00
     ```

2. **更新 state.json 字段**
   - `current_step` = 当前步骤名称（如："proposal"、"delta-spec"、"delta-design"、"tasks"、"validation"）
   - `{文档名}.status` = "completed"（或 "modified" 如果是修订）
   - `{文档名}.version` = 当前版本号（首次生成时为 1，修订时为原版本号）
   - `{文档名}.last_modified` = **当前实际时间**（ISO8601 格式，北京时间）
   - `last_action` = "生成 {文档名}"（或修订时的描述）
   - `next_action` = 下一步操作描述
   - 在 `history` 数组中添加新记录

3. **展示更新结果**
   - 使用状态展示模板展示当前进度
   - 提示用户下一步操作

**注意事项**：
- **必须使用当前实际时间**，禁止使用示例时间或硬编码时间
- 文档版本号管理：
  - 首次生成：version = 1
  - 修订：version 不变（iteration +1）
  - 重新生成：version +1
- history 数组必须按时间顺序追加新记录，不能覆盖或删除旧记录

---

### 状态展示模板

每次交互开始时，AI 应该展示当前状态：

```
📊 当前进度：
   ✅ 步骤 1：proposal.md（已完成，版本 1）
   🔄 步骤 2：delta-spec.md（进行中）
   ⏳ 步骤 3：delta-design.md（待开始）
   ⏳ 步骤 4：tasks.md（待开始）
   ⏳ 步骤 5：validation.md（待开始）

📁 已生成文件：
   - proposal.md（最后修改：{{实际修改时间}}）

🎯 下一步：
   交互澄清 delta-spec 的业务规则细节

💡 可用指令：
   - "查看进度" 或 "show progress"：显示当前进度和状态
   - "查看历史" 或 "show history"：显示操作历史
   - "回退到步骤 X" 或 "back to step X"：回退到指定步骤
   - "重新开始" 或 "restart"：清空状态，重新开始
```

---

### 状态转换规则

| 当前状态 | 用户指令 | 新状态 | 说明 |
|---------|---------|--------|------|
| proposal | "生成 delta-spec" | delta-spec | 进入步骤2，必须交互澄清 |
| delta-spec | "修订 proposal" | proposal | 回到步骤1，iteration+1，proposal.md status=modified |
| delta-spec | "生成 delta-design" | delta-design | 进入步骤3，必须交互澄清 |
| delta-design | "更新 delta-spec" | delta-spec | 回到步骤2，iteration+1，delta-spec.md status=modified |
| delta-design | "生成 tasks" | tasks | 进入步骤4，必须交互澄清 |
| tasks | "修订 delta-design" | delta-design | 回到步骤3，iteration+1，delta-design.md status=modified |
| tasks | "验证一致性" | validation | 进入步骤5 |
| validation | "调整 tasks" | tasks | 回到步骤4，iteration+1，tasks.md status=modified |
| validation | "完成" | completed | 工作流结束 |
| 任意 | "回退到步骤 X" | 步骤 X | 修改 current_step，记录跳转历史 |
| 任意 | "重新开始" | proposal | 清空所有状态，iteration=1 |

**重要规则**：
- 每次修订时，iteration +1
- 修订时只更新受影响的文件状态为 `modified`
- 跳转时在 history 中记录跳转操作
- 回退时保留已生成的文档，不删除

---

### 状态管理指令

用户可以使用以下指令查询和管理工作流状态：

| 指令 | 说明 | 示例 |
|------|------|------|
| "查看进度" / "show progress" | 显示当前进度和状态 | 查看进度 |
| "查看历史" / "show history" | 显示操作历史 | 查看历史 |
| "回退到步骤 X" / "back to step X" | 回退到指定步骤（1-5） | 回退到步骤 2 |
| "重新开始" / "restart" | 清空状态，重新开始 | 重新开始 |
| "保存状态" / "save state" | 手动保存当前状态 | 保存状态 |
| "当前状态" / "current state" | 显示完整的 state.json 内容 | 当前状态 |

---

### 上下文状态跟踪

在对话中维护以下关键信息：

**状态跟踪变量**：
- `current_step`: 当前步骤（0-5）
- `work_dir`: 当前工作目录（如 `US202601010015-增加逻辑多租`）
- `qa_progress`: 各步骤问答进度记录
- `generated_docs`: 已生成的文档列表
- `last_action`: 上次执行的操作（问答/生成/跳转）

---

### 重入恢复逻辑

当 skill 被重新激活时，执行以下检测：

1. **检测对话历史中的最后状态信息**
2. **扫描 `./codespec/changes/` 目录**，查找最近的工作目录
3. **检查工作目录下已存在的文档**
4. **识别当前处于哪个步骤**

**重入检测流程**：
```
如果对话历史中有状态信息：
  → 恢复 last_action 和 qa_progress
  → 提示用户："检测到未完成的工作，当前在步骤 X，是否继续？"
否则：
  → 扫描 changes/ 目录，找到最近的工作目录
  → 检查已生成的文档
  → 推测当前步骤（如已有 proposal.md 但无 delta-spec.md → 步骤 2）
  → 提示用户："发现工作目录 {work_dir}，已生成 {docs}，是否继续？"
```

**详细的重入恢复逻辑**：详见 [references/common-guidance.md](references/common-guidance.md)

---

## 执行原则与遵从性要求

### 交互式澄清的强制执行

**核心原则**：每个步骤的"交互式澄清"阶段是必须执行的，不能跳过。

**执行规则**：
1. **必须执行**：进入任何步骤后，必须先完成对应的"交互式澄清"阶段
2. **分段进行**：每次提问 2-3 个问题，等待用户回复后继续下一轮
3. **进度跟踪**：记录每轮问答的完成状态，支持中断后恢复
4. **完成标志**：只有当所有必要问题都得到回答后，才能进入"生成文档"阶段

**禁止行为**：
- ❌ 在未完成交互式澄清的情况下直接生成文档
- ❌ 一次性提问超过 3 个问题
- ❌ 跳过"交互式澄清"阶段直接进入"生成文档"阶段
- ❌ 在用户未回答完所有关键问题时就终止问答

**完成判断标准**：
- 所有核心问题都得到了用户的明确回答
- 收集到的信息足以生成符合输出标准的文档
- 用户明确表示可以继续或表示"可以生成文档了"

**交互工具选择**:
- 如果是**opencode** agent，**必须**使用`question`工具，**禁止**直接列举问题
- 如果是**relay** agent，如果有`ask_user`工具，则**必须**使用`ask_user`工具，**禁止**直接列举问题
- 对于其他agent，如果有结构化问答交互工具，必须使用，否则可以列举问题。

### 文档生成的时机

**文档生成必须在以下条件满足后才能执行**：
1. 交互式澄清阶段已完成
2. 收集到的信息满足该步骤的"输出标准"
3. 用户未提出需要继续澄清的问题

### 🔴 用户确认的强制执行

**核心原则**：步骤 1-4 的文档生成后，必须等待用户确认才能进入下一步。

**执行规则**：
1. **必须执行**：文档生成完成后，必须进入"用户确认"阶段
2. **确认方式**：向用户展示确认请求，等待用户明确回复
3. **确认选项**：
   - "确认" 或 "继续" → 文档状态设置为 confirmed，进入下一步
   - "修改: [具体修改意见]" → 根据反馈调整文档，状态保持 generated
   - "重新生成" → 重新生成文档，version+1，状态保持 generated
4. **禁止行为**：
   - ❌ 在文档生成后直接进入下一步
   - ❌ 在用户未确认的情况下设置文档状态为 completed
   - ❌ 跳过用户确认环节
5. **确认标志**：只有当用户明确回复"确认"或"继续"时，才能将文档状态设置为 confirmed 并进入下一步

**确认提示模板**：
```markdown
✅ {文档名} 已生成

📍 文档位置: {文档路径}

📋 请 review 文档内容，确认是否符合预期

💡 可用指令：
- "确认" 或 "继续" → 确认文档，进入下一步
- "修改: [具体修改意见]" → 根据您的反馈调整文档
- "重新生成" → 重新生成当前文档
- "查看文档" → 显示文档完整内容

⏸️ 等待您确认后再继续...
```

### 步骤 5 的特殊要求

**步骤 5（一致性验证）的特殊性**：
- ❌ **不进行交互式澄清**：步骤 5 不需要向用户提问，AI 自主完成所有分析
- ✅ **AI 自主分析**：AI 必须自主执行文档链检查、遗漏检查、一致性检查等所有验证工作
- ✅ **主动发现问题**：AI 应主动识别文档链中的所有问题，不需要用户提示
- ✅ **提供明确建议**：AI 应给出具体的修订建议，明确指出需要修订的步骤
- ✅ **引导用户决策**：AI 应呈现完整的问题分析，让用户基于事实做出是否修订的决策

**步骤 5 的执行规则**：
1. **自主完成检查**：不向用户询问"是否有问题"，而是自主检查
2. **问题分类明确**：按严重程度（严重/一般/建议）分类问题
3. **修订建议具体**：每个问题都应指向具体的修订步骤
4. **结论明确**：必须给出明确的验证结论（通过/有警告/不通过）

---

## 上下文状态管理

本 skill 支持多次重入场景，需要维护以下状态信息：

### 状态跟踪变量

在对话中维护以下关键信息：

**状态跟踪**:
- `current_step`: 当前步骤（0-5）
- `work_dir`: 当前工作目录（如 `US202601010015-增加逻辑多租`）
- `qa_progress`: 各步骤问答进度记录
- `generated_docs`: 已生成的文档列表
- `last_action`: 上次执行的操作（问答/生成/跳转）

### 重入恢复逻辑

当 skill 被重新激活时，执行以下检测：

1. **检测对话历史中的最后状态信息**
2. **扫描 `./codespec/changes/` 目录**，查找最近的工作目录
3. **检查工作目录下已存在的文档**
4. **识别当前处于哪个步骤**

**重入检测流程**：
```
如果对话历史中有状态信息：
  → 恢复 last_action 和 qa_progress
  → 提示用户："检测到未完成的工作，当前在步骤 X，是否继续？"
否则：
  → 扫描 changes/ 目录，找到最近的工作目录
  → 检查已生成的文档
  → 推测当前步骤（如已有 proposal.md 但无 delta-spec.md → 步骤 2）
  → 提示用户："发现工作目录 {work_dir}，已生成 {docs}，是否继续？"
```

**详细的重入恢复逻辑**：详见 [references/common-guidance.md](references/common-guidance.md)

---

## 步骤 0：工作目录识别

### 执行时机
- 工作流程开始时自动执行
- 用户首次使用 skill 时
- 重入时需要确认工作目录

**注意**：步骤 0 不需要场景识别，因为所有场景都需要相同的工作目录识别流程。

### 工作流程

1. **目录结构确认与创建**
   - 检查 `{root}/codespec` 目录是否存在
   - 如果不存在，自动创建 `codespec` 目录及其子目录：
     - `specs/` - 存放全量规格和设计文档
     - `changes/` - 存放工作目录（各个 story 的设计文档）
     - `archives/` - 存放已归档的工作目录

2. **工作目录识别**
   - 如果用户明确给出开发任务描述：
     - 扫描 `{root}/codespec/changes` 目录（排除 archives 子目录）
     - 查找与任务描述相似的工作目录
     - 如果找到相似的工作目录，请用户确认是否使用该目录
     - 如果没有找到相似的工作目录或用户选择不使用，请求用户提供工作目录名称（格式：`US编号-功能名`）并自动创建
   - 如果用户没有给出开发任务描述：
     - 请求用户提供开发任务描述或工作目录名称

3. **工作目录创建规范**
   - 工作目录必须创建在 `{root}/codespec/changes/` 目录下
   - 工作目录名称格式：`US编号-功能名`
   - 示例：`{root}/codespec/changes/US202601010001-初始化服务项目框架`
   - **禁止在项目根目录下直接创建工作目录**（如：`{root}/US202601010001-初始化服务项目框架`）

4. **全量规格确认**
   - 检查 `{root}/codespec/specs/spec.md` 是否存在
   - 如果不存在，提示用户优先使用 [codewiki](https://codewiki.rnd.huawei.com/projects) 生成专业文档并手工归档
   - 如果期望在本地生成文档，选择合适的 skill 生成并按 codespec 规范归档

**异常处理**：详见 [references/exception-handling.md](references/exception-handling.md)

---

## 步骤 1：需求澄清（proposal.md）

### 认知目标
将模糊的需求转化为清晰的需求证据。

### 执行时机
- 用户触发："启动story设计"、"开始SDD设计"、"生成 proposal"、"编写需求澄清文档"
- 步骤 0 完成后自动进入

### 工作流程

#### 第一阶段：收集初始需求
- 询问用户：当前的 story 背景、目标用户、核心功能
- 记录关键信息：业务场景、技术约束、优先级

#### 第二阶段：交互式澄清（必须执行）
- 使用问答逻辑（见 [references/q-a-proposal.md](references/q-a-proposal.md)）进行深度澄清
- **场景识别**：首先识别 story 类型（业务需求/设计分解/技术改进），选择合适的问答策略
  - **业务需求场景**：聚焦"为什么做"，询问业务价值和目标用户
  - **设计分解场景**：聚焦"如何实现"，跳过"为什么做"，直接问技术约束和实施范围
  - **技术改进场景**：聚焦技术方案和改进目标
- **问答分段**：每次提问 2-3 个问题，单次回复控制在 30 行以内
- **进度跟踪**：记录问答进度，支持中断后恢复

#### 第三阶段：生成 proposal.md
- 使用 [templates/proposal.md](templates/proposal.md) 模板
- 包含：背景与动机、变更内容、影响分析、DFX约束

#### 第四阶段：更新状态
- 按照[通用状态更新规范](#通用状态更新规范)更新 state.json
- 展示当前进度和下一步操作
- 提示用户："✅ proposal.md 已生成，下一步：生成 delta-spec.md（需要交互澄清）"
 
### 状态管理
- 完成后自动更新 state.json
- 展示当前进度（使用状态展示模板）
- 提示用户下一步操作
 
**进度展示模板：**
```
📊 当前进度：
   ✅ 步骤 1：proposal.md（已生成，待确认，版本 1）
   🔄 步骤 2：delta-spec.md（待开始）
   ⏳ 步骤 3：delta-design.md（待开始）
   ⏳ 步骤 4：tasks.md（待开始）
   ⏳ 步骤 5：validation.md（待开始）
  
📁 文档状态：
   - proposal.md（状态：⏸️ 已生成，待确认，版本 1，最后修改：[时间戳]）
  
🎯 当前任务：
   等待用户确认 proposal.md
  
💡 可用指令：
   - "确认" 或 "继续" → 确认文档，进入下一步：生成 delta-spec.md（需要交互澄清）
   - "修改: [具体修改意见]" → 根据您的反馈调整文档
   - "重新生成" → 重新生成当前文档
   - "查看文档" → 显示文档完整内容
```
### 输出标准
- ✅ 问题清晰度：能否用一句话描述"我们解决的是什么问题"？
- ✅ 范围边界明确："做什么"和"不做什么"的边界是否清晰？
- ✅ 可设计性：是否提供了足够的技术设计输入？
- ✅ 可测量性：是否定义了功能点、里程碑、完成标志？

**详细问答逻辑**：详见 [references/q-a-proposal.md](references/q-a-proposal.md)

---

## 步骤 2：增量规格定义（delta-spec.md）

### 认知目标
将需求证据转化为可验收的业务规则增量。

### 执行时机
- 用户触发："生成 delta-spec"、"编写增量规格"、"更新规格文档"
- 步骤 1 完成后自动进入

### 工作流程

#### 第一阶段：准备全量规格
- 读取 `codespec/specs/spec.md` 获取项目总体设计信息
- 分析现有规格的结构和内容，识别与修改规格相关的部分

#### 第二阶段：交互式澄清（必须执行）
- 使用问答逻辑（见 [references/q-a-delta-spec.md](references/q-a-delta-spec.md)）进行深度澄清
- 对比 proposal.md 与全量规格，识别变更点
- 按照 ADDED/MODIFIED/REMOVED 语义组织内容
- **场景识别**：根据 story 类型调整提问重点
- **问答分段**：每次提问 2-3 个问题，单次回复控制在 30 行以内
- **进度跟踪**：记录问答进度，支持中断后恢复

#### 第三阶段：生成 delta-spec.md
- 使用 [templates/delta-spec.md](templates/delta-spec.md) 模板
- 包含：ADDED Requirements、MODIFIED Requirements、REMOVED Requirements、数据约束变更

#### 第四阶段：校验 delta-spec.md
- 将输出的 delta-spec.md 内容与系统既有实现做对照分析
- 检查是否会破坏系统的设计，是否有不一致的设计

#### 第五阶段：更新状态
- 按照[通用状态更新规范](#通用状态更新规范)更新 state.json

### 输出标准
- ✅ ADDED：新规则是否覆盖了 proposal.md 的所有功能点？
- ✅ MODIFIED：修改是否基于 SPEC.md 的现有规则，而非重新定义？
- ✅ REMOVED：删除是否有明确的原因和归档计划？
- ✅ 可验证性：每条规则是否都有明确的验收条件？
- ✅ 边界清晰：是否保持了 Spec vs Design 的边界？

**详细问答逻辑**：详见 [references/q-a-delta-spec.md](references/q-a-delta-spec.md)

---

## 步骤 3：增量设计（delta-design.md）

### 认知目标
将业务规则转化为可实施的技术方案。

### 执行时机
- 用户触发："生成 delta-design"、"编写增量设计"、"更新设计文档"
- 步骤 2 完成后自动进入

### 工作流程

#### 第一阶段：读取全量设计
- 询问用户：全量设计文档路径（如 `codespec/specs/design.md`）
- 分析现有设计的架构和模块划分

#### 第二阶段：交互式澄清（必须执行）
- 使用问答逻辑（见 [references/q-a-delta-design.md](references/q-a-delta-design.md)）进行深度设计探讨
- 基于 delta-spec.md，识别需要变更的设计模块
- **场景识别**：根据变更类型调整提问重点（数据模型/接口/流程）
- **问答分段**：每次提问 2-3 个问题，单次回复控制在 30 行以内
- **进度跟踪**：记录问答进度，支持中断后恢复

#### 第三阶段：生成 delta-design.md
- 使用 [templates/delta-design.md](templates/delta-design.md) 模板
- 包含：设计背景、设计决策、数据模型变更、接口设计变更、流程设计、风险与缓解

#### 第四阶段：更新状态
- 按照[通用状态更新规范](#通用状态更新规范)更新 state.json

### 输出标准
- ✅ 技术选型：是否有方案对比和选择理由？
- ✅ 数据模型：是否考虑了与现有模型的兼容性？
- ✅ 接口设计：是否向后兼容（如需修改）？
- ✅ 风险评估：是否识别了关键风险和缓解方案？
- ✅ 可实施性：DDL 语句是否准备好执行？
- ✅ 可追溯性：技术方案是否与 delta-spec.md 的业务规则保持一致？

**详细问答逻辑**：详见 [references/q-a-delta-design.md](references/q-a-delta-design.md)

---

## 步骤 4：开发任务规划（tasks.md）

### 认知目标
将技术方案拆分为 AI Agent 可执行的任务。

### 执行时机
- 用户触发："生成 tasks"、"规划开发任务"、"编写任务清单"
- 步骤 3 完成后自动进入

### 工作流程

#### 第一阶段：交互式澄清（必须执行）
- 使用问答逻辑（见 [references/q-a-tasks.md](references/q-a-tasks.md)）进行深度任务分析
- 基于 delta-design.md，识别开发单元
- 按照依赖关系排序任务
- **场景识别**：根据技术复杂度调整任务粒度
- **问答分段**：每次提问 2-3 个问题，单次回复控制在 30 行以内
- **进度跟踪**：记录问答进度，支持中断后恢复

#### 第二阶段：任务粒度控制
- 建议每个任务 1-4 小时可完成
- 每个任务对应一次代码提交（<2000 行）
- 任务可独立测试和验证
- 任务描述应具体到文件/模块级别

#### 第三阶段：生成 tasks.md
- 使用 [templates/tasks.md](templates/tasks.md) 模板
- 包含：数据模型、领域层、应用层、基础设施层、接口层、测试、文档更新、验证、任务依赖关系

#### 第四阶段：更新状态
- 按照[通用状态更新规范](#通用状态更新规范)更新 state.json

### 输出标准
- ✅ 单一职责：每个任务专注一个文件或模块
- ✅ 可执行性：任务描述是否具体到文件/模块级别？
- ✅ 验证标准：是否定义了"怎么算完成"？
- ✅ 测试覆盖：每个业务规则是否至少有一个测试用例？
- ✅ 可追溯性：任务是否引用 delta-spec.md 和 delta-design.md？

**详细问答逻辑**：详见 [references/q-a-tasks.md](references/q-a-tasks.md)

---

## 步骤 5：一致性验证（validation.md）

### 认知目标
自主检查前面步骤的工作质量，识别问题并提供修复建议，确保文档链的一致性和完整性。

### 执行时机
- 用户触发："生成 validation"、"一致性验证"、"检查文档链"
- 步骤 4 完成后自动进入

### 工作流程

**重要说明**：
- 本步骤是 AI 自主分析和检测，不进行交互式澄清
- 详细执行指南见 [references/step-5-validation.md](references/step-5-validation.md)
- 执行时请先加载该 reference 文件

#### 工作流程概要

1. **读取所有相关文档**
   - 读取全部 6 个文档（全量规格/设计 + 4 个增量文档）

2. **AI 自主分析（必须执行）**
   - 文档链对应关系检查
   - 遗漏检查
   - 一致性检查
   - 完整性检查
   - 可实施性检查
   - 与基线文档兼容性检查

3. **生成 validation.md**
   - 使用 [templates/validation.md](templates/validation.md) 模板

4. **提供修订建议和跳转选项（必须执行）**
   - 给出验证结论（通过/有警告/不通过）
   - 列出问题摘要（按优先级排序）
   - 提供修订建议（明确指向需要修订的步骤）
   - 询问用户是否需要修订

#### 第四阶段：更新状态
- 按照[通用状态更新规范](#通用状态更新规范)更新 state.json
- `current_step` 设置为 "completed"
- `next_action` 设置为 "SDD 设计流程已完成！可以开始执行 tasks.md 中的开发任务"

### 输出标准
- ✅ 文档链对应关系清晰完整，每条需求都能追溯到任务
- ✅ 遗漏问题明确列出，按优先级排序
- ✅ 与基线文档兼容性检查完成，无破坏性变更
- ✅ 修复建议具体可执行，明确指向需要修订的步骤
- ✅ 验证结论明确（通过/有警告/不通过）

### AI 自主性要求
- **不向用户提问**：AI 自主完成所有检查，不询问用户"是否有问题"
- **主动发现问题**：AI 应主动识别文档链中的所有问题
- **提供明确建议**：AI 应给出具体的修订建议，而不是模糊的提示
- **引导用户决策**：AI 应呈现完整的问题分析，让用户基于事实做出决策

---

## 步骤跳转与接续机制

### 支持的跳转操作

用户可以随时跳转到任意步骤：

```
"修订 proposal" → 跳转到步骤 1
"更新 delta-spec" → 跳转到步骤 2
"修改 delta-design" → 跳转到步骤 3
"调整 tasks" → 跳转到步骤 4
"验证一致性" → 跳转到步骤 5
"跳到步骤 X" → 直接跳转到指定步骤
```

### 跳转触发词识别

识别以下触发词模式：
- "修订"、"更新"、"修改"、"调整" + 文档名 → 跳转到对应步骤
- "跳到"、"转到"、"去" + 步骤名 → 跳转到指定步骤
- "继续"、"接着做" → 基于当前状态继续

### 跳转前的检查

在执行跳转前，检查以下条件：

1. **前置条件检查**
   - 跳转到步骤 2：需要 proposal.md 存在
   - 跳转到步骤 3：需要 delta-spec.md 存在
   - 跳转到步骤 4：需要 delta-design.md 存在
   - 跳转到步骤 5：需要 tasks.md 存在

2. **上下文恢复**
   - 读取跳转目标步骤的已生成文档
   - 恢复该步骤的问答进度（qa_progress）
   - 提示用户："已跳转到步骤 X，当前进度：{progress}，是否继续？"

### 修订后的流程

**正常流程**（首次执行或无问题）：
- 步骤 1 → 步骤 2 → 步骤 3 → 步骤 4 → 步骤 5 → 完成

**验证发现问题后的修订循环**：
详见 [references/step-5-validation.md](references/step-5-validation.md) 中的"修订循环机制"章节

---

## 问答分段机制

### 分段原则

**单次提问控制**：
- 每次提问不超过 3 个问题
- 单次回复总行数控制在 30 行以内
- 问题较多时，拆分为多轮对话逐步推进

**渐进式披露**：
- 根据用户反馈动态调整后续问题
- 优先问核心问题，再问细节问题
- 避免一次性加载所有问题

### 问答进度跟踪

**进度记录格式**：
```
[步骤 1 问答进度]
- 第 1 轮：业务背景、目标用户 ✅
- 第 2 轮：功能范围、验收标准 ✅
- 第 3 轮：影响分析、DFX约束 ✅
```

**重入时的问答恢复**：
- 检查 qa_progress 记录
- 跳过已完成的问题
- 从未完成的问题继续提问

### 通用引导技巧

详细技巧详见 [references/common-guidance.md](references/common-guidance.md)

---

## 异常处理机制

### 异常场景处理

本 skill 定义了以下异常场景的处理流程：

1. **全量规格文档缺失**
2. **工作目录不存在**
3. **模板文件缺失**
4. **用户回答冲突**
5. **文档生成失败**
6. **问答进度丢失**
7. **跳转条件不满足**
8. **文档验证失败**
9. **上下文过大**
10. **用户中断**

详细的异常处理流程详见 [references/exception-handling.md](references/exception-handling.md)

### 处理原则

- **友好提示**：清晰的错误信息和建议
- **多选项提供**：提供多个解决方案供用户选择
- **状态保持**：尽可能保持已生成的内容和进度
- **日志记录**：记录异常信息便于调试
- **优雅降级**：在部分功能不可用时仍然能够继续工作

---

## 输出示例

详细的输出示例详见 [references/output-examples.md](references/output-examples.md)

---

## 工具和资源

### 使用的模板
- [templates/proposal.md](templates/proposal.md) - 需求澄清模板
- [templates/delta-spec.md](templates/delta-spec.md) - 增量规格模板
- [templates/delta-design.md](templates/delta-design.md) - 增量设计模板
- [templates/tasks.md](templates/tasks.md) - 任务规划模板
- [templates/validation.md](templates/validation.md) - 一致性验证模板

### 参考文档
- [references/common-guidance.md](references/common-guidance.md) - 通用引导技巧、上下文状态管理、重入恢复逻辑
- [references/sdd-methodology.md](references/sdd-methodology.md) - SDD 方法论背景、设计原则、文档侧重点
- [references/output-examples.md](references/output-examples.md) - 输出示例
- [references/exception-handling.md](references/exception-handling.md) - 异常场景处理
- [references/q-a-proposal.md](references/q-a-proposal.md) - 需求澄清问答逻辑
- [references/q-a-delta-spec.md](references/q-a-delta-spec.md) - 增量规格问答逻辑
- [references/q-a-delta-design.md](references/q-a-delta-design.md) - 增量设计问答逻辑
- [references/q-a-tasks.md](references/q-a-tasks.md) - 任务规划问答逻辑
- [references/step-5-validation.md](references/step-5-validation.md) - 步骤 5 一致性验证详细指南