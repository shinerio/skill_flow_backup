import argparse
import json
import requests
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


def upload_document(feature: str, category: str, file_path: str) -> dict:
    """
    上传文档到云捷桌面

    Args:
        feature (str): 云捷设计桌面的feature id， 如 FE2026021300012
        category (str): 文档类型，支持: proposal, 增量Spec, 增量Design
        file_path (str): 文档文件路径

    Returns:
        dict: 返回成功的结果

    Raises:
        ValueError: 当category不是支持的类型或文件不存在时
        requests.RequestException: 当HTTP请求失败时
    """
    # 验证category是否为支持的类型
    valid_categories = ['proposal', '增量Spec', '增量Design']
    if category not in valid_categories:
        raise ValueError(f"不支持的category类型: {category}, 支持的类型: {valid_categories}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise ValueError(f"读取文件失败: {e}")

    # 构建请求URL
    url = f"{CLOUDSCOPE_URL_PREFIX}design-desktop-management/api/sdd/design/edit"

    # 构建请求体
    payload = {
        "entitySn": feature,
        "paragraphs": [
            {
                "category": category,
                "content": content
            }
        ]
    }

    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    # 发送POST请求
    response = requests.post(url, json=payload, headers=headers, verify=False)

    # 检查响应状态码
    response.raise_for_status()

    # 解析响应
    result = response.json()

    # 检查返回的code是否为200
    if result.get('code') != 200:
        raise requests.RequestException(f"上传失败: {result.get('message')}")

    # 返回成功的数据部分
    return result.get('data', {})


def main():
    """
    命令行入口函数
    使用方法:
        python upload_document.py --feature FE2026021300011 --category proposal --file_path ./document.txt
    """
    parser = argparse.ArgumentParser(description='上传文档到云捷桌面')
    parser.add_argument('--feature', type=str, required=True, help='云捷设计桌面的feature id，如 FE2026021300011')
    parser.add_argument('--category', type=str, required=True,
                        choices=['proposal', '增量Spec', '增量Design'],
                        help='文档类型: proposal, 增量Spec, 增量Design')
    parser.add_argument('--file_path', type=str, required=True, help='文档文件路径')
    parser.add_argument('--output', type=str, choices=['json', 'pretty'], default='pretty',
                        help='输出格式: json (紧凑JSON) 或 pretty (格式化JSON)')

    args = parser.parse_args()

    try:
        # 调用上传函数
        result = upload_document(args.feature, args.category, args.file_path)

        # 根据输出格式返回结果
        if args.output == 'json':
            print(json.dumps(result))
        else:
            print(json.dumps(result, indent=4, ensure_ascii=False))

        print("\n上传成功!")
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
    exit(main())

