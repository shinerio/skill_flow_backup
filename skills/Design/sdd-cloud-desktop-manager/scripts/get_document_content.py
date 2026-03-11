import requests
import re
import os

# 获取当前文件所在目录，然后读取config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.py')

# 动态加载config模块
spec = __import__('importlib.util').util.spec_from_file_location('config', config_path)
config = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config)
AUTH = config.AUTH
CLOUDSCOPE_URL_PREFIX = config.CLOUDSCOPE_URL_PREFIX

# 文档名称映射关系
DOCUMENT_NAME_MAPPING = {
    "proposal": "proposal",
    "增量Spec": "delta-spec",
    "增量Design": "delta-design"
}


def get_document_content(wiki_sn: str, output_dir: str) -> list:
    """
    获取文档内容并保存到本地md文档

    Args:
        wiki_sn: 文档序列号
        output_dir: 输出目录路径（必传，由agent从工作空间目录中获取）

    Returns:
        list: 成功信号列表，包含保存的文件路径
    """
    try:
        url = f"{CLOUDSCOPE_URL_PREFIX}devops-knowledge-management/api/wiki"

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH
        }

        params = {
            "sn": wiki_sn,
            "type": "UI",
            "filterClassify": "FEATURE_API_DESIGN"
        }

        response = requests.get(url, params=params, headers=headers, verify=False)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                data = result.get("data", {})
                paragraphs = data.get("paragraphs", [])

                # 创建输出目录
                os.makedirs(output_dir, exist_ok=True)
                success_signals = []
                for paragraph in paragraphs:
                    paragraph_name = paragraph.get("documentName", "")
                    content = paragraph.get("content", "")

                    # 检查是否是这三个文档之一，如果不是则跳过
                    if paragraph_name not in DOCUMENT_NAME_MAPPING:
                        continue

                    # 去除HTML标签，只保留纯文本内容
                    clean_content = re.sub(r'<[^>]+>', '', content)

                    # 使用映射关系获取文件名，如果没有映射则使用原始名称
                    safe_filename = DOCUMENT_NAME_MAPPING.get(paragraph_name, paragraph_name)
                    # 生成安全的文件名
                    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', safe_filename)
                    if not safe_filename:
                        safe_filename = f"document_{len(success_signals) + 1}"

                    # 保存为md文件
                    file_path = os.path.join(output_dir, f"{safe_filename}.md")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(clean_content)

                    success_signals.append({
                        "status": "success",
                        "file_path": file_path,
                        "paragraph": paragraph_name
                    })

                return success_signals

        return [{"status": "failed", "message": "Failed to fetch document content"}]

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return [{"status": "failed", "message": f"Request exception: {e}"}]
    except Exception as e:
        print(f"未知异常: {e}")
        return [{"status": "failed", "message": f"Unknown exception: {e}"}]


def main():
    import sys
    if len(sys.argv) < 3:
        print("请提供 wiki_sn 和 output_dir 参数")
        print("用法: python get_document_content.py <wiki_sn> <output_dir>")
        sys.exit(1)

    wiki_sn = sys.argv[1]
    output_dir = sys.argv[2]
    result = get_document_content(wiki_sn, output_dir)
    print(result)


if __name__ == '__main__':
    main()
