1. 将本次聊天对话的所有内容输出到chats目录下，新建文件名为YYYY-MM-DD-HH-mm-SS.txt
执行 git diff HEAD 获取当前所有未提交的文件变更内容，生成修改内容摘要{{generated_summary}}，和一句简单的修改主题{{generated_title}}。
1. 按以下格式追加到changelog文件末尾。changelog备份地址为changelog/change_YYYYMM.md（每个月生成一个change log）。如果文件不存在，则按命名要求创建。
## {{generated_title}}
date: YYYY-MM-DD
{{generated_summary}}
2. 按新增changelog相同格式用作git commit的message
 - 执行 git add -A
 - 执行 git commit -m 
 - 然后执行 git push 推送到远程仓库