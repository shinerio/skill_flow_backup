import requests
import os
import sys

# 获取当前文件所在目录的父目录，然后读取config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.py')

# 动态加载config模块
spec = __import__('importlib.util').util.spec_from_file_location('config', config_path)
config = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config)
AUTH = config.AUTH
CLOUDSCOPE_URL_PREFIX = config.CLOUDSCOPE_URL_PREFIX

def get_clouddevops_info(entity_sn: str, timeout=30):
    """
    HTTP GET 请求函数

    Args:
        entity_sn: 云捷的FE开头的编号
        timeout: 超时时间(秒),默认为30

    Returns:
        dict: 服务器响应
    """
    url = f"{CLOUDSCOPE_URL_PREFIX}design-desktop-management/api/design/feature/relation?entitySn={entity_sn}&type=Feature"
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


if __name__ == '__main__':
    import sys

    # 检查是否提供了命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python get_clouddevops_info.py <entity_sn>")
        print("示例: python get_clouddevops_info.py \"FE2026021300012\"")
        sys.exit(1)

    # 获取命令行参数
    entity_sn = sys.argv[1]

    # 调用函数
    response = get_clouddevops_info(entity_sn=entity_sn)

    if "error" in response:
        print(f"请求失败: {response['error']}")
        if response.get("status_code"):
            print(f"状态码: {response['status_code']}")
    else:
        print(f"请求成功!")
        print(f"响应数据: {response}")
