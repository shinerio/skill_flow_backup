import sys
import requests
import os
from dataclasses import dataclass, asdict
from typing import List, Optional

# 获取当前文件所在目录，然后读取config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.py')

# 动态加载config模块
spec = __import__('importlib.util').util.spec_from_file_location('config', config_path)
config = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config)
AUTH = config.AUTH
CLOUDSCOPE_URL_PREFIX = config.CLOUDSCOPE_URL_PREFIX


@dataclass
class UserInfo:
    """用户信息类"""
    id: str
    name: str
    account: str

    def to_dict(self):
        """转换为字典格式"""
        return asdict(self)


def get_primary_reviewer(domain_id):
    """
    获取主审人信息 - 提交设计评审任务

    Args:
        domain_id: 云捷域ID

    Returns:
        dict: 服务器响应,包含主审人信息
    """
    api_url = f"{CLOUDSCOPE_URL_PREFIX}vision-platform/api/domains/2/group-members/batch?group=knowledge_primary_reviewer_group&needFaltung=true"


    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    payload = [domain_id]

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }


def extract_primary_reviewer(response_data):
    """
    从响应数据中提取主审人信息

    Args:
        response_data: API响应数据,格式如下:
            {
                "code": 200,
                "message": "Success",
                "data": {
                    "29500": [
                        {
                            "type": "Core",
                            "user": {
                                "status": null,
                                "id": 206923,
                                "username": "wwx984429",
                                "name_full": "wukai WX984429",
                                "name": "吴凯",
                                "account": "WX984429",
                                "email": "wukai60@h-partners.com",
                                "office_name": null,
                                "user_type": null,
                                "password": null,
                                "address": null,
                                "private_token": null
                            },
                            "role": {...},
                            "user_id": "206923",
                            "domain_id": 29500
                        }
                    ]
                }
            }

    Returns:
        dict: 格式如下:
            {
                "code": 200,
                "message": "Success",
                "data": [
                    {"id": "206923", "name": "吴凯", "account": "WX984429"},
                    ...
                ]
            }
    """
    # 检查是否有错误
    if isinstance(response_data, dict) and "error" in response_data:
        return {
            "code": 500,
            "message": response_data.get("error", "Unknown error"),
            "data": []
        }

    try:
        # 检查响应格式
        if not isinstance(response_data, dict):
            return {
                "code": 400,
                "message": "Invalid response format",
                "data": []
            }

        code = response_data.get("code")
        message = response_data.get("message", "Success")
        data = response_data.get("data", {})

        # 检查code是否为200
        if code != 200:
            return {
                "code": code,
                "message": message,
                "data": []
            }

        # 提取用户信息列表
        user_list: List[UserInfo] = []

        if isinstance(data, dict):
            # 遍历所有域的用户数据
            for domain_id, reviewers in data.items():
                if isinstance(reviewers, list):
                    for reviewer in reviewers:
                        if isinstance(reviewer, dict):
                            # 获取user对象中的信息
                            user_info = reviewer.get("user")
                            if isinstance(user_info, dict):
                                # 提取id, name, account字段
                                user_id = str(user_info.get("id", ""))
                                name = user_info.get("name", "")
                                account = user_info.get("account", "")

                                # 创建UserInfo对象
                                user = UserInfo(id=user_id, name=name, account=account)
                                user_list.append(user)

        # 转换为字典列表
        result_data = [user.to_dict() for user in user_list]

        return {
            "code": 200,
            "message": "Success",
            "data": result_data
        }

    except (AttributeError, KeyError, TypeError) as e:
        return {
            "code": 500,
            "message": f"Error processing response: {str(e)}",
            "data": []
        }


def main():
    """主函数 - 从命令行参数获取 domain_id"""
    # 检查是否提供了命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python get_primary_reviewer.py <domain_id>")
        print("示例: python get_primary_reviewer.py \"29500\"")
        sys.exit(1)

    # 获取 domain_id 参数
    domain_id = sys.argv[1]

    # 调用 API 获取主审人信息
    response_data = get_primary_reviewer(domain_id)
    result = extract_primary_reviewer(response_data)
    print(result)


if __name__ == '__main__':
    main()
