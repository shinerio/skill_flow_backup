import requests
import json
import os
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


def get_user_clouddevops_id_list(username_list: list) -> list:
    """
    根据工号列表获取普通评审人列表

    Args:
        username_list (list): 用户工号列表，如 ['l00932730', 'z00933666']

    Returns:
        list: 返回普通评审人列表，如 [{'id': '206923', 'name': '吴凯', 'account': 'WX984429'}]

    Raises:
        requests.RequestException: 当HTTP请求失败时
        ValueError: 当用户列表为空或响应格式不正确时
    """
    # 检查用户列表是否为空
    if not username_list:
        raise ValueError("用户工号列表不能为空")

    # 将用户列表转换为逗号分隔的字符串
    user_info = ','.join(username_list)

    # 构建请求URL
    url = f"{CLOUDSCOPE_URL_PREFIX}devops-user/api/v1/query/batch/users?userInfo={user_info}"

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
        raise requests.RequestException(f"获取用户列表失败: {result.get('message')}")

    # 提取data中的用户列表
    user_list = result.get('data', [])

    # 检查是否有用户数据
    if not user_list:
        raise ValueError(f"未找到工号为 {username_list} 的用户")

    # 构建普通评审人列表
    reviewer_list = []
    for user in user_list:
        reviewer = {
            'id': user.get('id'),
            'name': user.get('name'),
            'account': user.get('account')
        }
        reviewer_list.append(reviewer)

    return reviewer_list


def main():
    """
    命令行入口函数
    使用方法:
        python get_user_clouddevops_id_list.py l00932730,z00569045
    """
    try:
        # 检查是否提供了命令行参数
        if len(sys.argv) < 2:
            print("使用方法: python get_user_clouddevops_id_list.py 工号1,工号2,工号3")
            print("示例: python get_user_clouddevops_id_list.py l00932730,z00569045")
            return 1

        # 从命令行参数获取工号列表
        username_list = sys.argv[1].split(',')

        # 获取多个用户的评审人信息
        reviewer_list = get_user_clouddevops_id_list(username_list)
        print(f"工号列表 {username_list} 的评审人信息:")
        for reviewer in reviewer_list:
            print(f"  ID: {reviewer['id']}, 姓名: {reviewer['name']}, 账号: {reviewer['account']}")
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
