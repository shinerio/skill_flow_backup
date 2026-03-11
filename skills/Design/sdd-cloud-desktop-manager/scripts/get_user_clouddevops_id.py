import requests
import json
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

def get_username_from_auth():
    url = f"{CLOUDSCOPE_URL_PREFIX}vision-platform/api/auth/token/check"
    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        "user_token": AUTH
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        response.raise_for_status()  # 抛出异常如果HTTP请求返回了不成功的状态码
        response_data = response.json()

        if response_data['code'] == 200 and response_data['message'] == 'Success':
            username = response_data['data']['username']
            return username
        else:
            print("Error: ", response_data['message'])
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_user_clouddevops_id(username: str) -> int:
    """
    根据工号获取用户的云捷ID

    Args:
        username (str): 用户工号，如 "l00932730"

    Returns:
        int: 返回用户的云捷ID，如 887091

    Raises:
        requests.RequestException: 当HTTP请求失败时
        ValueError: 当用户不存在或响应格式不正确时
    """
    # 构建请求URL
    url = f"{CLOUDSCOPE_URL_PREFIX}devops-user/api/v1/query/batch/users?userInfo={username}"

    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 发送GET请求
    response = requests.get(url, headers=headers, verify=False)

    # 检查响应状态码
    response.raise_for_status()

    # 解析响应
    result = response.json()

    # 检查返回的code是否为200
    if result.get('code') != 200:
        raise requests.RequestException(f"获取用户ID失败: {result.get('message')}")

    # 提取data中的用户列表
    user_list = result.get('data', [])

    # 检查是否有用户数据
    if not user_list:
        raise ValueError(f"未找到工号为 {username} 的用户")

    # 获取第一个用户的ID
    user_id = user_list[0].get('id')

    if user_id is None:
        raise ValueError(f"用户数据中缺少ID字段")

    return user_id

def main():
    """
    命令行入口函数
    使用方法:
        python get_user_clouddevops_id.py
    """
    try:
        # 调用获取用户云捷ID函数
        username = get_username_from_auth()
        if not username:
            print(f"auth token可能为空或过期，username获取失败")
        user_id = get_user_clouddevops_id(username)
        print(f"工号 {username} 的云捷ID: {user_id}")
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


if __name__ == '__main__':
    main()