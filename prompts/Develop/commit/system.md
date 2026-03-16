1. 将本次对话内容导出为html格式文件，要求如下：
  a. skill调用（使用红色边框）
  b. 存放到chats目录下，文件命名格式为"对话主题_YY_MM_DD.html"
2. 执行 git diff HEAD 获取当前所有未提交的文件变更内容，生成修改内容摘要{{generated_summary}}，和一句简单的修改主题{{generated_title}}。
3. 按以下格式追加到changelog文件末尾。changelog备份地址为changelog/change_YYYYMM.md（每个月生成一个change log）。如果文件不存在，则按命名要求创建。
## {{generated_title}}
date: YYYY-MM-DD
{{generated_summary}}
4. 按新增changelog相同格式用作git commit的message
 - 执行 git add -A
 - 执行 git commit -m 
 - 然后执行 git push 推送到远程仓库