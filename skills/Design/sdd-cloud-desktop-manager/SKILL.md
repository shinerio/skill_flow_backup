---
name: sdd-cloud-desktop-manager
description: SDD云捷设计桌面统一管理工具
function:
  - 1.获取用户工作项FE（feature）任务信息
  - 2.上传FE（feature）生成的sdd设计文档到云捷设计桌面
  - 3.从云捷设计桌面拉取FE（feature）的文档和评审意见
  - 4.根据评审意见修改文档并重新上传

使用场景:
   - 用户要求"获取feature"、"查看feature"或"选择feature"时,执行获取工作项流程
   - 用户上下文中提及"上传文档"或"提交文档"时,执行文档上传流程
   - 用户上下文中提及"拉取评审意见"或"获取评审意见"时,执行评审意见处理流程
   - 用户上下文中提及"处理评审反馈"或"修复/修改评审意见",执行评审意见处理流程
   - 用户意图不明确时,询问用户选择具体操作
---

# SDD云捷设计桌面统一管理工具

## 概述

本skill统一管理SDD设计文档在云捷设计桌面的所有操作,包括获取工作项、文档上传、评审意见拉取、评审意见修改和文档重新上传。

## 功能模块

本skill包含三个主要工作流程,根据用户触发条件自动选择:

### 流程A: 获取工作项

**别名**: 获取工作项

**触发条件**:
- 用户需要查看/获取工作项（feature或story）任务

  <!-- 用户在提及云捷设计桌面的上下文中提到"获取feature"、"查看feature"或"选择feature" -->

**工作流程**:
1. 获取用户云捷账号ID
2. 获取并展示Features列表（只展示第一页）

### 流程B: 文档上传

**触发条件**:
- 用户要求"上传云捷设计桌面"
- 用户要求"提交SDD评审"
- 用户在SDD文档上下文中提及"上传评审"或"提交评审"

**工作流程**:
1. 验证文档可用性(proposal.md、delta-spec.md、delta-design.md)
2. 获取云捷FE任务信息
3. 上传三个文档
4. 获取云捷重要标识信息
5. 生成设计文档URL
6. 报告完成状态

### 流程C: 评审意见处理

**触发条件**:
- 用户要求"拉取评审意见"
- 用户要求"修改评审意见"
- 用户要求"处理评审反馈"
- 用户要求"更新设计文档并上传"

**工作流程**:
1. 获取云捷FE任务信息
2. 获取云捷重要标识信息
3. 拉取评审意见和三个部分的文档(proposal、增量Spec、增量Design)
4. 让用户选择要修复的评审意见
5. 基于选择的评审意见修改文档
6. 确认修复效果(不满意则根据用户澄清再次修改)
7. 上传修改后的文档
8. 报告完成状态

## 流程选择逻辑

当skill被触发时,根据以下逻辑选择执行哪个流程:

```
用户请求分析:
├─ 包含"获取feature"、"查看feature"、"选择feature" → 执行流程A(获取工作项)
├─ 包含"上传"、"提交评审"、"上传评审" → 执行流程B(文档上传)
├─ 包含"拉取评审意见"、"修改评审意见"、"处理评审意见"、"更新设计文档" → 执行流程C(评审意见处理)
└─ 无法判断 → 询问用户意图
   └─ 使用ask_followup_question让用户选择:
      1. 获取工作项
      2. 上传SDD文档并提交评审
      3. 拉取评审意见并修改文档
```

## 详细工作流程

### 流程A: 获取工作项

**注意 铁律**:

- 只要执行到步骤n，就代表步骤n之前的所有步骤已经执行成功，不要再回头执行！**非常重要**

- 每一个功能脚本都在script中，不需要agent自己写python文件脚本
- 每一步的工作显示当前所处的步骤！结束一个步骤不要重复执行上一个
- 脚本没有问题，一定不要修改脚本！
- **流程控制铁律**：
  - 步骤执行顺序：步骤1 → 步骤2 → **结束**
  - **严禁从任何步骤跳回步骤1**
  - 每个步骤完成后，必须立即进入下一个步骤，不得重复执行已完成的步骤
  - 步骤2完成后，整个流程**必须结束**，不得继续执行任何步骤
  - 如果需要重新开始，必须由用户明确要求，agent不得自动重启流程
  - **交互确认后必须进入下一步骤，不得停留在当前步骤或返回前面的步骤**
- 维护一个已完成步骤的json文档，已完成的任务放到该json文档中，每次执行任务时查看该文档执行到哪一步，不能重复执行步骤

#### 步骤 1：获取用户云捷账号ID

**流程控制**：此步骤为流程的起始步骤，完成后必须进入步骤2，不得跳转到其他步骤。

按照工号获取用户的云捷id（工号在script/config.py中）

使用script/get_user_clouddevops_id.py这个脚本获取用户云捷id

input: 无

output：

- 用户云捷账号id（举例：887091）

```
python scripts/get_user_clouddevops_id.py
```

```
# 参考示例
python scripts/get_user_clouddevops_id.py
```

获取到用户云捷账号ID后，立即进入步骤2，不要在此步骤停留或等待用户确认。

#### 步骤 2：获取并展示Features列表（只展示第一页）

**流程控制**：此步骤完成后必须立即终止，不得跳回任何前面的步骤，也不得继续执行任何其他操作。

根据之前获得的用户云捷id，使用script/get_user_features.py这个脚本获取用户相关的features列表

**展示规则**：
- 默认展示 5 个 feature（第一页）
- 显示格式：序号. 特性编号 - 空间标题 - 任务标题
- 展示完毕后询问用户是否需要重新展示指定数量的条目

**执行流程**：

**(1) 获取features总数**

使用script/get_features_count.py这个脚本获取features总数：

input：

- 用户云捷id（举例：887091）
- 每页数量（默认为5）

output：

- features总数和总页数信息
  - `total_pages`: 总页数
  - `total_records`: 总记录数

```
python scripts/get_features_count.py <user_id> --page_size 5
```

```
# 参考示例
python scripts/get_features_count.py 887091 --page_size 5
```

向用户展示总数信息。

**(2) 获取并展示第一页数据（默认5条）**

调用脚本获取第一页数据（页码1，每页5个）：

input：

- 用户云捷id（举例：887091）
- 页码（默认为1）
- 每页数量（默认为5）

output：

- features的列表
  - 列表里有多个json，每个json有3个key ：
    - `number`: 特性编号（例如：FE2026021400004）
    - `space_title`: 空间标题（从返回体的 `simple_domain.title` 获取，例如：吴凯测试空间1aas）
    - `task_title`: 任务标题（从返回体的 `title` 获取，例如：ljx_test2）

```
python scripts/get_user_features.py <user_id> --page 1 --page_size 5
```

```
# 参考示例
python scripts/get_user_features.py 887091 --page 1 --page_size 5
```

**(3) 询问用户下一步操作**

**强制要求**：必须使用ask_followup_question工具，以选项点选的方式询问用户下一步操作，不得使用自由输入方式。

选项包括：
- 重新展示（让用户选择展示多少条）
- 结束查看

**(4) 根据用户选择执行**

- 如果用户选择"重新展示"：
  - 使用ask_followup_question工具让用户选择要展示的条数（提供预设选项：3条、5条、10条、20条）
  - 调用脚本获取第一页数据（页码1，用户选择的条数）
  - 展示该页数据
  - 再次询问用户是否需要重新展示其他数量的条目
  - 如果用户选择"结束查看"，则结束流程

- 如果用户选择"结束查看"：
  - 立即结束流程

**重要铁律**：
- 此步骤完成后，整个流程**必须结束**
- agent必须停止执行，不得跳回任何前面的步骤
- 不得继续执行任何其他操作
- 不得重复任何已完成的步骤
- 这是整个skill的最后一步，执行完毕后必须完全终止

**使用示例**：

**用户请求**："请帮我获取云捷设计桌面的feature列表。"

**预期响应（默认展示5条）**：

```
我将为您获取云捷设计桌面的feature列表。

正在获取您的云捷账号ID... ✅
您的云捷账号ID：887091

正在获取features总数... ✅
共找到 12 个 features

正在获取第1页数据... ✅

您的features列表如下（展示前 5 条）：
1. FE2026021400004 - 吴凯测试空间1aas - ljx_test2
2. FE2026021300012 - 测试空间2 - 测试任务
3. FE2026021100008 - 开发空间 - 开发任务
4. FE2026021000005 - 研发空间 - 研发任务
5. FE2026020900003 - 测试空间1 - 测试任务1

已为您展示 5 个 features（共 12 个）
```

**询问用户**：

```
请选择下一步操作：
1. 重新展示（选择展示条数）
2. 结束查看
```

**用户选择"重新展示"后**：

```
请选择要展示的条数：
1. 展示 3 条
2. 展示 5 条
3. 展示 10 条
4. 展示 20 条
```

**用户选择"展示 10 条"后**：

```
正在获取第1页数据... ✅

您的features列表如下（展示前 10 条）：
1. FE2026021400004 - 吴凯测试空间1aas - ljx_test2
2. FE2026021300012 - 测试空间2 - 测试任务
3. FE2026021100008 - 开发空间 - 开发任务
4. FE2026021000005 - 研发空间 - 研发任务
5. FE2026020900003 - 测试空间1 - 测试任务1
6. FE2026020800002 - 开发空间A - 开发任务A
7. FE2026020700001 - 测试空间B - 测试任务B
8. FE2026020600009 - 研发空间C - 研发任务C
9. FE2026020500007 - 集成空间 - 集成任务
10. FE2026020400006 - 验证空间 - 验证任务

已为您展示 10 个 features（共 12 个）
```

**再次询问用户**：

```
请选择下一步操作：
1. 重新展示（选择展示条数）
2. 结束查看
```

**用户选择"结束查看"后**：

```
✅ features列表已为您展示完毕（共 12 个）
```

**如果features少于等于5个**：

```
我将为您获取云捷设计桌面的feature列表。

正在获取您的云捷账号ID... ✅
您的云捷账号ID：887091

正在获取features总数... ✅
共找到 3 个 features

正在获取第1页数据... ✅

您的features列表如下（展示前 5 条）：
1. FE2026021400004 - 吴凯测试空间1aas - ljx_test2
2. FE2026021300012 - 测试空间2 - 测试任务
3. FE2026021100008 - 开发空间 - 开发任务

已为您展示 3 个 features（共 3 个）

✅ features列表已为您展示完毕（共 3 个）
```

### 流程B: 文档上传

**注意 铁律**:

- 只要执行到步骤n,就代表步骤n之前的所有步骤已经执行成功,不要再回头执行！**非常重要**

- 每一个功能脚本都在script中,不需要agent自己写python文件脚本
- 每一步的工作显示当前所处的步骤！结束一个步骤不要重复执行上一个
- 脚本没有问题,一定不要修改脚本！

- **流程控制铁律**:
  - 步骤执行顺序:步骤1 → 步骤2 → 步骤3 → 步骤4 → 步骤5 → 步骤6 → **结束**()
  - **严禁从任何步骤跳回步骤1或步骤2**
  - 每个步骤完成后,必须立即进入下一个步骤,不得重复执行已完成的步骤
  - 步骤8完成后,整个流程**必须结束**,不得继续执行任何步骤
  - 如果需要重新开始,必须由用户明确要求,agent不得自动重启流程
  - **交互确认后必须进入下一步骤,不得停留在当前步骤或返回前面的步骤**

#### 步骤1: 验证文档可用性

**流程控制**:此步骤为流程的起始步骤,完成后必须进入步骤2,不得跳转到其他步骤。

检查当前项目中是否存在三个必需的SDD文档:

三个文档的位置一般在<当前项目目录>/codespec/changes/\<变更任务>(如US202601010001-Serverless作业按量计费能力) 下

如果没有,用户需要澄清指定文件

- `proposal.md` - SDD提案文档
- `delta-spec.md` - 变更规格文档
- `delta-design.md` - 变更设计文档

如果缺少任何文档,请告知用户并询问是使用可用文档继续,还是先生成缺失的文档,或者指出文档的实际位置。**交互确认**

查找好路径后和用户确认。**强制要求:必须使用ask_followup_question工具,以选项点选的方式和用户确认,不得使用自由输入方式。用户确认后立即进入步骤2,不要在此步骤停留或重复执行**。

#### 步骤2: 获取云捷FE(feature)任务信息

**触发条件**：如果用户已经明确告知需要上传的FE信息（如：FE2026022600054），跳过此步骤。**非常重要**

**流程控制**：此步骤完成后必须进入步骤3,不得跳回任何前面的步骤。

**(1)按照工号获取用户的云捷id**

使用script/get_user_clouddevops_id.py这个脚本获取用户id

input: 无 (username在config中)

output:

- 用户云捷账号id(举例:887091)

```
python get_user_clouddevops_id.py
```

```
# 参考示例
python get_user_clouddevops_id.py
```

**(2)根据用户的云捷id,获取对应的features列表**

根据之前获得的用户云捷id,使用script/get_user_features.py这个脚本获取用户相关的features列表

input:

- 用户云捷id(举例:887091)

output:

- features的列表
  - 列表里有多个json,每个json有3个key:
    - `number`: 特性编号(例如:FE2026021400004)
    - `space_title`: 空间标题(从返回体的`simple_domain.title`获取,例如:吴凯测试空间1aas)
    - `task_title`: 任务标题(从返回体的`title`获取,例如:ljx_test2)

```
python get_user_features.py <user_id>
```

```
# 参考示例
python get_user_features.py 887091
```

响应完,展示给用户,让用户选择操作哪一个feature **交互确认**。

**强制要求:必须使用ask_followup_question工具,以选项点选的方式让用户选择feature,不得使用自由输入方式。**

#### 步骤3: 上传文档

**流程控制**:此步骤完成后必须进入步骤4,不得跳回任何前面的步骤。

对于三个文档中的**每一个**,调用上传脚本(upload_document.py脚本在script中):

要将三个文档分别上传,分别读取本地的proposal.md, delta-spec.md, delta-design.md,读取内容转化为string类型,放到input的content中

**注意**

- 一定要匹配好,本地的delta-spec.md文件对应云捷桌面的增量Spec类别
- 本地的delta-design.md文件对应云捷桌面的增量Design类别

input:

- feature编号 (同entity_sn,举例FE2026021300012)
- category类别 (只有3种:proposal, 增量Spec, 增量Design)
- file_path文件路径

output:

- 上传成功的响应

```
python scripts/upload_document.py --feature <feature> --category <category> --file_path <file_path>
```

```bash
# 参考示例
python scripts/upload_document.py --feature FE2026021300011 --category delta-design --file_path "./delta-design.md"
```

**注意**:得到上传成功success的response后再执行下一个步骤,否则重试

**重要**:完成三个文档的上传后,立即进入步骤4,不要在此步骤停留或等待用户确认。标志该上传文档内容已完成

#### 步骤4: 获取云捷重要标识信息

**流程控制**:此步骤完成后必须进入步骤5,不得跳回任何前面的步骤。

获取该设计桌面的**云捷重要标识信息**

获取feature(同entity_sn)后,需要使用script中的脚本get_clouddevops_info.py获取其他相关的**云捷重要信息**

input:

- feature编号 (同entity_sn,举例FE2026021300012)

output:

- 云捷域id(同assignedDomain, domain_id 举例 29500)
- wiki的id (同wiki_id, 举例 2025640584)
- wiki的编号(wiki_sn 举例 WIKI2026021300013)

**注意**:要保存好这些output信息,**非常重要**下文中也会使用！！！

```
python get_clouddevops_info.py <feature>
```

```
# 参考示例
python get_clouddevops_info.py FE2026021300012
```

注意:响应数据得到云捷域id (assignedDomain),wiki的id (wikiId),wiki的编号(wikiSn)这三个主要信息,提供给下面的接口使用。

#### 步骤5: 生成设计文档URL

**流程控制**:此步骤完成后必须进入步骤6,不得跳回任何前面的步骤。

根据步骤4获取的云捷信息,拼接云捷设计桌面的URL并展示给用户。

**URL拼接规则**:

使用以下信息拼接URL:
- 云捷域id (domain_id, 例如: 29500)
- feature编号 (FENumber, 例如: FE2026022600020)

URL格式:
```
https://clouddevops.huawei.com/domains/{domain_id}/design_desktop/my-design/todo?domainId={domain_id}&FENumber={FENumber}
```

**示例**:
如果 domain_id = 29500, FENumber = FE2026022600020,则拼接后的URL为:
```
https://clouddevops.huawei.com/domains/29500/design_desktop/my-design/todo?domainId=29500&FENumber=FE2026022600020
```

**执行流程**:

1. 根据步骤4获取的信息,拼接完整的URL
2. **向用户展示可点击的超链接格式URL**（使用Markdown链接格式：`[URL文本](URL地址)`）
3. 提示用户可以直接点击该超链接访问云捷设计桌面

**展示格式要求**:
- 必须使用Markdown超链接格式：`[云捷设计桌面访问链接](https://clouddevops.huawei.com/domains/{domain_id}/design_desktop/my-design/todo?domainId={domain_id}&FENumber={FENumber})`
- 用户可以直接点击链接跳转到云捷设计桌面

**重要**:完成URL生成和展示后,立即进入步骤6,不要在此步骤停留或等待用户确认。

#### 步骤6: 报告完成状态

**流程控制**:此步骤是整个流程的最后一步,完成后必须立即终止,不得跳回任何前面的步骤,也不得继续执行任何其他操作。

根据用户在步骤6的选择,提供不同的完成报告:

**情况1: 用户选择使用skill提交评审**

向用户提供摘要:
- 已上传的文档:proposal.md、delta-spec.md、delta-design.md
- 评审提交状态
- 遇到的任何错误或警告

**情况2: 用户选择手动上传**

向用户提供摘要:
- 已上传的文档:proposal.md、delta-spec.md、delta-design.md
- 云捷设计桌面URL
- 提示用户需要手动访问云捷设计桌面URL进行评审提交操作

**重要铁律**:
- 此步骤完成后,整个流程**必须结束**
- agent必须停止执行,不得跳回任何前面的步骤
- 不得继续执行任何其他操作
- 不得重复任何已完成的步骤
- 这是整个流程B的最后一步,执行完毕后必须完全终止

### 流程C: 评审意见处理

**注意 铁律**:

- 每一个功能脚本都在script中,不需要agent自己写python文件脚本
- 每一步的工作显示当前所处的步骤！结束一个步骤不要重复执行上一个
- 脚本没有问题,一定不要修改脚本！

#### 步骤1: 获取云捷FE(feature)任务信息

**触发条件**：如果用户已经明确告知需要上传的FE信息（如：FE2026022600054），跳过此步骤。**非常重要**

**(1)按照工号获取用户的云捷id**

使用script/get_user_clouddevops_id.py这个脚本获取用户id

input: 无 (username在config中)

output:

- 用户云捷账号id(举例:887091)

```
python get_user_clouddevops_id.py
```

```
# 参考示例
python get_user_clouddevops_id.py
```

**(2)根据用户的云捷id,获取对应的features列表**

根据之前获得的用户云捷id,使用script/get_user_features.py这个脚本获取用户相关的features列表

input:

- 用户云捷id(举例:887091)

output:

- features的列表
  - 列表里有多个json,每个json有3个key:
    - `number`: 特性编号(例如:FE2026021400004)
    - `space_title`: 空间标题(从返回体的`simple_domain.title`获取,例如:吴凯测试空间1aas)
    - `task_title`: 任务标题(从返回体的`title`获取,例如:ljx_test2)

```
python get_user_features.py <user_id>
```

```
# 参考示例
python get_user_features.py 887091
```

响应完,展示给用户,让用户选择操作哪一个feature **交互确认**

**强制要求**:必须使用ask_followup_question工具,以选项点选的方式让用户选择feature,不得使用自由输入方式。

#### **步骤2: 获取云捷重要标识信息**

获取feature(同entity_sn)后,需要使用script中的脚本get_clouddevops_info.py获取其他相关的**云捷重要信息**

input:

- feature编号 (同entity_sn,举例FE2026021300012)

output:

- 云捷域id(同assignedDomain, domain_id 举例 29500)
- wiki的id (同wiki_id, 举例 2025640584)
- wiki的编号(wiki_sn 举例 WIKI2026021300013)

```
python get_clouddevops_info.py <feature>
```

```
# 参考示例
python get_clouddevops_info.py FE2026021300012
```

注意:响应数据得到云捷域id (assignedDomain),wiki的id (wikiId),wiki的编号(wikiSn)这三个主要信息,提供给下面的接口使用

#### 步骤3: 拉取评审意见

**(1)从<当前项目目录>/codespec/changes/下查找feature对应<变更任务>目录**。**必须执行**

**(2)调用scripts/get_document_content.py中的接口函数,从云捷设计桌面拉取文档并保存到<当前项目目录>/codespec/changes/<变更任务>目录下:**

只拉取以下三个部分的文档:

- proposal.md 文档内容
- delta-spec.md 文档内容
- delta-design.md 文档内容

使用脚本get_document_content.py (在script中)

input:

- wiki的编号(wiki_sn,举例:WIKI2026021300013)
- output_dir(必传):输出目录路径,设置为<当前项目目录>/codespec/changes/<变更任务>(如:US202601010001-Serverless作业按量计费能力)
  - 一般情况下,这个文件夹下都有这些文件,直接覆盖掉
- paragraphs(必传):指定要拉取的文档类别,设置为["proposal", "增量Spec", "增量Design"]

output:

- 成功信号列表(包含文件路径),例如:[{"status": "success", "file_path": ".../codespec/changes/US202601010001-Serverless作业按量计费能力/proposal.md", "paragraph": "proposal"}, ...]

```
python get_document_content.py <wiki_sn> <output_dir> --paragraphs proposal 增量Spec 增量Design
```

```
# 参考示例
python get_document_content.py WIKI2026021400003 "D:/workcode/MagicLamp_VibeSddSuite/0226/MagicLamp_VibeSddSuite/codespec/changes/US202601010001-Serverless作业按量计费能力" --paragraphs proposal 增量Spec 增量Design
```

**重要说明**:此步骤只拉取proposal、增量Spec、增量Design三个部分的文档,不拉取其他文档。

**(2)调用scripts/get_reviews_content.py中的接口函数,从云捷设计桌面拉取到本地:**

- 评审意见(评审反馈内容)

使用脚本get_reviews_content.py (在script中)

input:

- wiki的id (同wiki_id,entity_id, 举例 2025640584 | 使用步骤2获得的)

output:

- 意见的列表(包含多个json,每个json包含review_content和name_full)

```
python get_reviews_content.py <entity_id>
```

```
# 使用示例
python get_reviews_content.py 2025640584
```

列出这些意见,并标号,方便用户选择(意见用表格形式展示,规整易读)

#### 步骤4: 让用户选择要修复的评审意见

展示拉取到的所有评审意见,让用户选择需要修复的意见:

- 以清晰的格式列出所有评审意见(编号、内容、涉及的文档)
- **强制要求**:必须使用ask_followup_question工具,以选项点选的方式让用户选择要修复的评审意见,不得使用自由输入方式
- 用户可以选择修复部分或全部评审意见

**执行主体**:用户交互

#### 步骤5: 基于选择的评审意见修改文档

AI Agent根据用户选择的评审意见,对三个文档进行智能修改:

- 分析选中的评审意见,识别需要修改的部分
- 逐个文档进行修改,确保修改内容准确回应评审意见
- 保持文档结构完整性和格式一致性
- 每次展示修复的diff的内容

**执行主体**:AI Agent

#### 步骤6: 确认修复效果

展示修改后的文档内容,让用户确认修复效果:

- 展示每个文档的主要修改点
- **强制要求**:必须使用ask_followup_question工具,以选项点选的方式询问用户是否满意修复效果,不得使用自由输入方式
- 如果用户不满意:
  - 收集用户的澄清和具体要求
  - AI Agent根据澄清再次修改文档
  - 重复确认过程,直到用户满意

**执行主体**:用户交互 + AI Agent(本skill)

#### 步骤7: 上传修改后的文档

用户确认满意后,调用scripts/upload_document.py中的上传接口,将修改后的三个文档重新上传到云捷设计桌面:

对于三个文档中的**每一个**,调用上传脚本(upload_document.py脚本在script中):

要将三个文档分别上传,分别读取<当前项目目录>/codespec/changes/<变更任务>目录下的proposal.md, delta-spec.md, delta-design.md,读取内容转化为string类型,放到input的content中

**注意**一定要匹配好:

- 本地的proposal.md文件对应云捷桌面的proposal类别
- 本地的delta-spec.md文件对应云捷桌面的增量Spec类别
- 本地的delta-design.md文件对应云捷桌面的增量Design类别
- 以上文件按顺序上传

input:

- feature编号 (同entity_sn,举例FE2026021300012)
- category类别 (只有3种:proposal, 增量Spec, 增量Design)
- file_path文件路径(指向<当前项目目录>/codespec/changes/<变更任务>目录下的对应文件)

output:

- 上传成功的响应

```
python scripts/upload_document.py --feature <feature> --category <category> --file_path <file_path>
```

```bash
# 参考示例
python scripts/upload_document.py --feature FE2026021300011 --category delta-design --file_path "D:/workcode/MagicLamp_VibeSddSuite/0226/MagicLamp_VibeSddSuite/codespec/changes/US202601010001-Serverless作业按量计费能力/delta-design.md"
```

**重要提示**:文档上传后,需要人工在云捷设计桌面点击"评审通过"才能继续后续流程。

#### 步骤8: 报告完成状态

向用户提供摘要:
- 拉取的评审意见数量和关键内容
- 用户选择的评审意见列表
- 修改的文档列表和主要修改点
- 修复确认过程的迭代次数
- 文档上传状态
- 提示:文档已上传,请在云捷设计桌面点击"评审通过"后才继续后续流程

**重要提示**:文档上传后,需要人工在云捷设计桌面点击"评审通过"才能继续后续流程。

## 资源结构

本skill包含以下资源:

### scripts/

包含用于云捷设计桌面操作的所有可执行脚本:

- `config.py` - 配置文件
- `get_clouddevops_info.py` - 根据feature获取云捷桌面的相关信息
  - 输入:feature
  - 输出:云捷域id(assignedDomain),wiki的id(wikiId),wiki的编号(wikiSn)
- `get_document_content.py` - 从云捷设计桌面拉取文档内容
  - 输入:wiki_sn, output_dir(路径为<当前项目目录>/codespec/changes/<变更任务>), paragraphs(指定要拉取的文档类别,如["proposal", "增量Spec", "增量Design"])
  - 输出:成功信号列表(包含文件路径)
- `get_primary_reviewer.py` - 获取主评审人列表
  - 输入:domain_id
  - 输出:主评审人列表
- `get_reviews_content.py` - 拉取评审意见
  - 输入:entity_id
  - 输出:评审意见列表
- `get_user_clouddevops_id.py` - 按照工号获取用户的云捷id
  - 输入:无(username在config中)
  - 输出:用户云捷账号id
- `get_user_clouddevops_id_list.py` - 批量获取用户云捷id
  - 输入:工号列表(逗号分隔)
  - 输出:用户云捷id列表
- `get_user_features.py` - 根据用户云捷id获取features列表
  - 输入:user_id
  - 输出:features的列表
- `submit_review.py` - 提交评审
  - 输入:wiki_sn, domain_id, entity_id, ordinary_reviewers, primary_reviewers
  - 输出:评审提交状态
- `upload_document.py` - 上传文档到云捷设计桌面
  - 输入:feature, category, file_path
  - 输出:上传状态

### assets/

存放必要的资源文件(目前为空)

## 使用示例

### 示例1: 获取工作项(流程A)

**用户请求**:"请帮我获取云捷设计桌面的feature列表。"

**系统识别**:包含"获取feature"关键词,执行流程A

**预期响应**:

```
我将为您获取云捷设计桌面的feature列表。

正在获取您的云捷账号ID... ✅
您的云捷账号ID：887091

正在获取features总数... ✅
共找到 12 个 features

正在获取第1页数据... ✅

您的features列表如下（展示前 5 条）：
1. FE2026021400004 - 吴凯测试空间1aas - ljx_test2
2. FE2026021300012 - 测试空间2 - 测试任务
3. FE2026021100008 - 开发空间 - 开发任务
4. FE2026021000005 - 研发空间 - 研发任务
5. FE2026020900003 - 测试空间1 - 测试任务1

已为您展示 5 个 features（共 12 个）
```

**询问用户**：

```
请选择下一步操作：
1. 重新展示（选择展示条数）
2. 结束查看
```
### 示例2: 上传文档(流程B)

**用户请求**:"请将SDD文档上传到云捷设计桌面进行评审。"

**系统识别**:包含"上传"关键词,执行流程B

**预期响应**:

```
我将把SDD文档上传到云捷设计桌面进行评审。

正在上传proposal.md... ✅
正在上传delta-spec.md... ✅
正在上传delta-design.md... ✅

正在提交评审... ✅

✅ 所有SDD文档已成功上传到云捷设计桌面并提交评审。
```

### 示例3: 处理评审意见(流程C)

**用户请求**:"帮我拉取评审意见并修改文档。"

**系统识别**:包含"拉取评审意见"和"修改文档"关键词,执行流程C

**预期响应**:

```
✅ 任务已完成

## 执行摘要

### 拉取数据
- 评审意见:12 条
- proposal.md:已拉取
- delta-spec.md:已拉取
- delta-design.md:已拉取

### 用户选择的评审意见
- [1] proposal.md 第 2.1 节缺少架构图说明
- [3] delta-spec.md 接口定义不清晰
- [5] delta-design.md 缺少异常处理流程
- [7] proposal.md 部署方案不完整

**共选择 4 条评审意见进行修复**

### 文档修改
- proposal.md:修改 3 处(新增架构图说明、补充部署方案、更新依赖项)
- delta-spec.md:修改 2 处(修正接口定义、补充参数说明)
- delta-design.md:修改 1 处(补充异常处理流程)

### 修复确认过程
- 第 1 次修改后确认:用户不满意,澄清"架构图需要更详细的标注"
- 第 2 次修改后确认:用户满意 ✅

**确认迭代次数:2 次**

### 文档上传
- proposal.md:✅ 上传成功
- delta-spec.md:✅ 上传成功
- delta-design.md:✅ 上传成功

---

📌 **重要提示**:文档已成功上传到云捷设计桌面。

⚠️ **下一步**:请在云捷设计桌面点击"评审通过",评审通过后才能继续后续的Story拆分和上传流程。
```

### 示例4: 意图不明确

**用户请求**:"云捷桌面操作"

**系统识别**:无法判断具体意图,询问用户

**预期响应**:

```
请问您需要执行哪种操作?

1. 获取工作项
2. 上传SDD文档并提交评审
3. 拉取评审意见并修改文档
```

## 错误处理

如果任何步骤失败:

### 流程A错误处理
- **用户云捷ID获取失败**:检查config.py中的username配置是否正确,或提示用户提供正确的工号
- **Features列表获取失败**:报告错误,建议检查网络连接或联系管理员

### 流程B错误处理
- **文档未找到**:告知用户缺少哪个文档,并建议先生成该文档
- **上传失败**:报告错误,如果可能则重试一次
- **提交失败**:报告错误,建议手动提交或重试
- **用户选择手动上传**:在步骤6如果用户选择手动上传,流程正常结束,不是错误

### 流程C错误处理
- **拉取失败**:报告错误,检查网络连接和权限
- **修改失败**:报告错误,根据用户澄清重新修改
- **上传失败**:报告错误,如果可能则重试一次

## 注意事项

1. **脚本实现**:本skill的scripts目录包含所有必要的脚本实现
2. **文档格式**:确保拉取和上传的文档格式一致(Markdown格式)
3. **授权认证**:脚本需要处理云捷平台的认证和授权逻辑
4. **错误处理**:脚本应包含适当的错误处理,并在失败时返回清晰的错误信息
5. **顺序执行**:严格按流程顺序执行,确保数据流转正确
6. **用户确认**:关键步骤必须等待用户确认,不能自动跳过
7. **强制交互方式**:所有用户交互确认步骤**必须使用ask_followup_question工具,以选项点选的方式与用户交互,严禁使用自由输入方式**
8. **迭代修改**:流程C的步骤5可能需要多次迭代,直到用户满意为止
9. **人工卡点**:文档上传后需要人工在云捷桌面点击"评审通过"才能继续后续流程
10. **流程选择**:根据用户请求的关键词自动选择执行流程A、流程B或流程C,如果无法判断则询问用户

## 优势

1. **一键复制**:用户只需复制整个skill目录到本机即可使用
2. **统一管理**:所有云捷桌面相关操作集中在一个skill中
3. **脚本复用**:避免重复脚本,所有脚本统一管理
4. **流程清晰**:根据用户意图自动选择合适的工作流程
5. **易于维护**:只需维护一个skill和一套脚本
6. **减少用户操作**:无需用户手动处理共享脚本
