import requests
import json
import sys
import os
import argparse

# 获取当前文件所在目录，然后读取config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.py')

# 动态加载config模块
spec = __import__('importlib.util').util.spec_from_file_location('config', config_path)
config = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(config)
AUTH = config.AUTH
CLOUDSCOPE_URL_PREFIX = config.CLOUDSCOPE_URL_PREFIX


def submit_review(wiki_sn: str, domain_id: str, entity_id: str, ordinary_reviewers: list, primary_reviewers: list):
    """
    提交评审功能

    Args:
        wiki_sn: wiki的编号 如 "WIKI2026021300013"
        domain_id: 云捷域ID 如 "29500"
        entity_id: 对应的FE的id 如 "2025640584"
        ordinary_reviewers: 普通评审人列表 如 [{"id": 887091, "username": "l00932730"}, ...]
        primary_reviewers: 主评审人列表 如 [{"id": 887091, "username": "l00932730"}, ...]

    Returns:
        str: 如果响应code为200且message为Success,返回"success",否则返回错误信息
    """
    url = f"{CLOUDSCOPE_URL_PREFIX}design-desktop-management/api/forward/processTask/submit?status=design"

    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH
    }

    payload = {
        "funcName": "reqDesign",
        "processBusinessKey": wiki_sn,
        "domainId": domain_id,
        "variables": {
            "status": "review",
            "param": {
                "wikiVO": {
                    "sn": wiki_sn,
                    "businessStatus": "review"
                },
                "countersignParams": {
                    "entity_sn": wiki_sn,
                    "type": "wiki",
                    "users": ordinary_reviewers,
                    "primaryReviewer": primary_reviewers,
                    "reviewer_checkpoint": 0,
                    "entity_id": entity_id,
                    "message_way": "create_group",
                    "remark": "邀请您进行文档评审，评审结束前：\n\n审核人鼠标选中正文给出评审意见，严重等级意见结束讨论后评审才能通过；\n主审人鼠标选中正文给出评审意见，评审为1票通过，1人结论通过评审结束。",
                    "url": f"{CLOUDSCOPE_URL_PREFIX}domains/2/design_desktop/my-design/review?domainId=2&FENumber=FE2026021300006",
                    "group_ids": [],
                    "classify": "review",
                    "send_welink_flag": False
                }
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 200 and result.get("message") == "Success":
            return "success"
        else:
            return result.get("message", "提交失败")
    except requests.exceptions.RequestException as e:
        return f"请求失败: {str(e)}"


def main():
    """
    命令行入口函数
    使用方法:
        python submit_review.py --wiki_sn WIKI2026021300013 --domain_id 29500 --entity_id 2025640584 --ordinary_reviewers '[{"id": 887091, "username": "l00932730"}]' --primary_reviewers '[{"id": 887091, "username": "l00932730"}]'
    """
    parser = argparse.ArgumentParser(description='提交评审功能')
    parser.add_argument('--wiki_sn', type=str, required=True, help='wiki的编号，如 WIKI2026021300013')
    parser.add_argument('--domain_id', type=str, required=True, help='云捷域ID，如 29500')
    parser.add_argument('--entity_id', type=str, required=True, help='对应的FE的id，如 2025640584')
    parser.add_argument('--ordinary_reviewers', type=str, required=True,
                        help='普通评审人列表，JSON格式字符串，如 \'[{"id": 887091, "username": "l00932730"}]\'')
    parser.add_argument('--primary_reviewers', type=str, required=True,
                        help='主评审人列表，JSON格式字符串，如 \'[{"id": 887091, "username": "l00932730"}]\'')

    args = parser.parse_args()

    def parse_json_with_fallback(json_str):
        """尝试解析JSON，支持多种格式"""
        # 方案1: 直接解析标准JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 方案2: 单引号替换双引号
        try:
            return json.loads(json_str.replace("'", '"'))
        except json.JSONDecodeError:
            pass

        # 方案3: 处理PowerShell去掉引号的情况，需要重建JSON
        # 匹配格式: [{id: 887091, username: l00932730}]
        import re
        pattern = r'\[\{id:\s*(\d+),\s*username:\s*(\w+)\}\]'
        match = re.match(pattern, json_str)
        if match:
            return [{"id": int(match.group(1)), "username": match.group(2)}]

        # 方案4: 处理多个评审人的情况
        pattern_multi = r'\[\{id:\s*(\d+),\s*username:\s*(\w+)\}(?:,\s*\{id:\s*(\d+),\s*username:\s*(\w+)\})*\]'
        if re.match(pattern_multi, json_str):
            reviewers = []
            # 提取所有的id和username对
            pairs = re.findall(r'id:\s*(\d+),\s*username:\s*(\w+)', json_str)
            for user_id, username in pairs:
                reviewers.append({"id": int(user_id), "username": username})
            return reviewers

        return None

    try:
        # 解析评审人列表
        ordinary_reviewers = parse_json_with_fallback(args.ordinary_reviewers)
        primary_reviewers = parse_json_with_fallback(args.primary_reviewers)

        if ordinary_reviewers is None:
            raise ValueError(f"无法解析普通评审人列表: {args.ordinary_reviewers}")
        if primary_reviewers is None:
            raise ValueError(f"无法解析主评审人列表: {args.primary_reviewers}")

        # 调用提交评审函数
        result = submit_review(args.wiki_sn, args.domain_id, args.entity_id, ordinary_reviewers, primary_reviewers)
        print(f"提交结果: {result}")
        return 0

    except ValueError as e:
        print(f"参数错误: {e}")
        return 1
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    main()