# -*- coding: utf-8 -*-
"""
PicGo Server Python Client - 通过路径上传图片
"""
import requests
import json
import sys
from pathlib import Path


class PicGoClient:
    """PicGo Server 客户端"""

    def __init__(self, host: str = "127.0.0.1", port: int = 36677):
        self.base_url = f"http://{host}:{port}"
        self.upload_url = f"{self.base_url}/upload"

    def upload(self, file_path: str) -> dict:
        """上传指定路径的图片文件"""
        # 转换为绝对路径
        abs_path = str(Path(file_path).resolve())

        payload = {"list": [abs_path]}
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            self.upload_url,
            data=json.dumps(payload),
            headers=headers
        )
        return response.json()


def main():
    if len(sys.argv) < 2:
        print("用法: python picgo_client.py <图片路径>")
        sys.exit(1)

    file_path = sys.argv[1]

    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"错误: 文件不存在: {file_path}")
        sys.exit(1)

    client = PicGoClient()
    result = client.upload(file_path)

    if result.get("success"):
        print(result["result"][0])
    else:
        print(f"上传失败: {result.get('message', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
