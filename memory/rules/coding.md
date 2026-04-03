# python

处理python依赖和脚本时，优先使用`uv`命令，禁止直接使用python命令，防止破坏系统环境。

# lsp

涉及代码定位、定义、引用、调用链等问题时，必须优先使用 LSP，不要直接先用 Grep/Glob，只有 LSP 不适用时再退回文本搜索。能使用lsp的场景必须优先使用lsp，lsp具有更快的速度和更高的准确率，lsp能提供但不限于以下能力。
- goToDefinition — 「processOrder 在哪里定义？」→ 确切的文件和行号
- findReferences — 「找到所有调用 validateUser 的地方」→ 每个调用点及其位置
- hover — 「config 变量是什么类型？」→ 完整的类型签名和文档
- documentSymbol — 「列出这个文件中的所有函数」→ 每个符号及其位置
- workspaceSymbol — 「找到 PaymentService 类」→ 在整个项目中搜索符号
- goToImplementation — 「哪些类实现了 AuthProvider？」→ 接口的具体实现
- incomingCalls/outgoingCalls — 「什么调用了 processPayment？」→ 完整的调用层次追踪