import requests
import json
import os
import argparse
import sys

# 获取当前文件所在目录，然后读取config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.py')

# 动态加载config模块
spec = __import__('importlib.util').util.spec_from_file_location('config', config_path)
config = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config)
AUTH = config.AUTH
CLOUDSCOPE_URL_PREFIX = config.CLOUDSCOPE_URL_PREFIX


def get_features_count(user_id: int, page_size: int = 5) -> dict:
    """
    获取用户的特性总数信息

    Args:
        user_id (int): 用户ID，如 887091
        page_size (int): 每页数量，默认为5

    Returns:
        dict: 返回特性总数信息，包含:
            - total_pages: 总页数
            - total_records: 总记录数

    Raises:
        requests.RequestException: 当HTTP请求失败时
        ValueError: 当响应格式不正确时
    """
    # 构建请求URL
    url = f"{CLOUDSCOPE_URL_PREFIX}devops-workitem/api/v1/query/workitems"

    # 构建请求体
    payload = {
        "first_filters": [
            {
                "key": "mine_todo",
                "operator": "||",
                "value": [user_id]
            }
        ],
        "sort": {
            "key": "updated_time",
            "value": "desc"
        },
        "select_field": [
            "simple_domain",
            "release_plans",
            "workitem_labels",
            "current_owners",
            "service_iteration"
        ],
        "pagination": {
            "current_page": 1,
            "page_size": page_size
        }
    }

    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 发送POST请求
    response = requests.post(url, json=payload, headers=headers, verify=False)

    # 检查响应状态码
    response.raise_for_status()

    # 解析响应
    result = response.json()

    # 检查返回的code是否为200
    if result.get('code') != 200:
        raise requests.RequestException(f"获取特性失败: {result.get('message')}")

    # 提取data中的分页信息
    data = result.get('data', {})

    # 只返回total_pages和total_records
    count_info = {
        "total_pages": data.get('total_pages', 0),
        "total_records": data.get('total_records', 0)
    }

    return count_info


def main():
    """
    命令行入口函数
    使用方法:
        python get_features_count.py 887091
        python get_features_count.py 887091 --page_size 10 --output json
    """
    parser = argparse.ArgumentParser(description='获取用户的特性总数')
    parser.add_argument('user_id', type=int, help='用户ID，如 887091')
    parser.add_argument('--page_size', type=int, default=5, help='每页数量，默认为5')
    parser.add_argument('--output', type=str, choices=['json', 'pretty'], default='pretty',
                        help='输出格式: json (紧凑JSON) 或 pretty (格式化JSON)')

    args = parser.parse_args()

    try:
        # 调用获取特性总数函数
        count_info = get_features_count(args.user_id, args.page_size)

        # 根据输出格式返回结果
        if args.output == 'json':
            print(json.dumps(count_info))
        else:
            print(json.dumps(count_info, indent=4, ensure_ascii=False))

        return 0

    except ValueError as e:
        print(f"参数错误: {e}")
        return 1
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return 1
    except Exception as e:
        print(f"发生未知错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
