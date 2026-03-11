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


def get_user_features(user_id: int, page: int = 1, page_size: int = 10) -> list:
    """
    获取用户的特性列表

    Args:
        user_id (int): 用户ID，如 887091
        page (int): 当前页码，默认为1
        page_size (int): 每页数量，默认为10

    Returns:
        list: 返回特性信息列表，每个元素是一个字典，包含:
            - number: 特性编号，如 "FE2026021400004"
            - space_title: 空间标题，如 "吴凯测试空间1aas"
            - task_title: 任务标题，如 "ljx_test2"

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
            "current_page": page,
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

    # 提取data中的result列表
    data = result.get('data', {})
    result_list = data.get('result', [])

    # 提取每个特性的信息
    features = []
    for item in result_list:
        if item.get('number'):
            feature_info = {
                "number": item.get('number'),
                "space_title": item.get('simple_domain', {}).get('title', ''),
                "task_title": item.get('title', '')
            }
            features.append(feature_info)

    return features

def main():
    """
    命令行入口函数
    使用方法:
        python get_user_features.py 887091
        python get_user_features.py 887091 --page 1 --page_size 10 --output json
    """
    parser = argparse.ArgumentParser(description='获取用户的特性列表')
    parser.add_argument('user_id', type=int, help='用户ID，如 887091')
    parser.add_argument('--page', type=int, default=1, help='当前页码，默认为1')
    parser.add_argument('--page_size', type=int, default=5, help='每页数量，默认为5')
    parser.add_argument('--output', type=str, choices=['json', 'pretty'], default='pretty',
                        help='输出格式: json (紧凑JSON) 或 pretty (格式化JSON)')

    args = parser.parse_args()

    try:
        # 调用获取特性函数
        features = get_user_features(args.user_id, args.page, args.page_size)

        # 根据输出格式返回结果
        if args.output == 'json':
            print(json.dumps(features))
        else:
            print(json.dumps(features, indent=4, ensure_ascii=False))

        print(f"\n共获取到 {len(features)} 个特性")
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