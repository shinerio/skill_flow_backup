执行 git diff HEAD 获取当前所有未提交的文件变更内容
综合分析对话上下文和 git diff 输出，生成修改内容摘要{{generated_summary}}，和一句简单的修改主题{{generated_title}}，然后按以下格式写入changelog和git commit中
## {{generated_title}}
date: YYYY-MM-DD
{{generated_summary}}
摘要应以 git diff 中的实际变更为准，对话上下文作为补充说明变更意图
changelog备份地址为changelog/change_YYYYMM.md（每个月生成一个change log）。如果文件不存在，则按命名要求创建。
执行 git add -A
执行 git commit -m
然后执行 git push 推送到远程仓库