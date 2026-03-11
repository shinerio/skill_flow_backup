import requests
import sys
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


def get_reviews_content(entity_id: int, type: str = "") -> list:
    """
    获取评审内容
    示例请求：

    Args:
        entity_id: 云捷任务ID
        type: 类型，默认为空""  countersign(结论) comment（意见评论）

    Returns:
        list: 包含评论的content和name_full的字典列表
    """
    try:
        url = f"{CLOUDSCOPE_URL_PREFIX}devops-knowledge-management/api/wiki/comments"

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH
        }

        payload = {
            "entity_id": entity_id,
            "type": type
        }

        response = requests.post(url, json=payload, headers=headers, verify=False)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                data = result.get("data", [])
                result_list = []

                for item in data:
                    comments = item.get("comments", [])
                    for comment in comments:
                        content = comment.get("content")
                        submitted_by = comment.get("submitted_by", {})
                        name_full = submitted_by.get("name_full")

                        if content and name_full:
                            result_list.append({
                                "review_content": content,
                                "name_full": name_full
                            })
                return result_list

        return []

    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return []
    except Exception as e:
        print(f"未知异常: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        print("请提供 entity_id 参数")
        print("用法: python get_reviews_content.py <entity_id>")
        print("示例: python get_reviews_content.py 2025640584")
        sys.exit(1)

    entity_id = sys.argv[1]
    result = get_reviews_content(entity_id)
    print(result)

if __name__ == '__main__':
    main()