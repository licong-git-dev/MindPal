#!/usr/bin/env python3
"""
MindPal API测试脚本
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    """测试登录"""
    print("\n=== 测试登录 ===")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"phone": "13900139000", "password": "test123456"}
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {result}")
    return result.get('data', {}).get('token')

def test_create_digital_human(token):
    """测试创建数字人"""
    print("\n=== 测试创建数字人 ===")
    response = requests.post(
        f"{BASE_URL}/api/digital-humans",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "小智",
            "avatar": "boy-sunny",
            "avatarEmoji": "👦",
            "personality": "gentle",
            "traits": {
                "liveliness": 70,
                "humor": 80,
                "empathy": 90,
                "initiative": 60,
                "creativity": 50
            },
            "voice": "xiaoyu",
            "voiceParams": {
                "speed": 1.0,
                "pitch": 0,
                "volume": 80
            }
        }
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: success={result.get('success')}, id={result.get('data', {}).get('id')}")
    return result.get('data', {}).get('id')

def test_list_digital_humans(token):
    """测试数字人列表"""
    print("\n=== 测试数字人列表 ===")
    response = requests.get(
        f"{BASE_URL}/api/digital-humans",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: success={result.get('success')}, count={len(result.get('data', []))}")
    return result.get('data', [])

def test_chat(token, dh_id):
    """测试对话（非流式，获取第一个chunk）"""
    print(f"\n=== 测试对话 (数字人ID: {dh_id}) ===")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"dhId": dh_id, "message": "你好！"},
            stream=True,
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        print("流式响应:")

        chunks = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if 'chunk' in data:
                        chunks.append(data['chunk'])
                        print(data['chunk'], end='', flush=True)
                    elif 'done' in data and data['done']:
                        print(f"\n情绪: {data.get('emotion')}")
                        break

        print(f"\n完整回复: {''.join(chunks)}")

    except Exception as e:
        print(f"错误: {e}")

def main():
    """主测试流程"""
    print("==> 开始测试MindPal API")

    # 1. 测试登录
    token = test_login()
    if not token:
        print("[FAIL] 登录失败，测试终止")
        return

    print(f"\n[OK] 获取到Token: {token[:30]}...")

    # 2. 测试数字人列表
    digital_humans = test_list_digital_humans(token)

    # 3. 测试创建数字人
    dh_id = test_create_digital_human(token)
    if not dh_id:
        print("[FAIL] 创建数字人失败")
        # 如果创建失败，使用现有的数字人
        if digital_humans:
            dh_id = digital_humans[0]['id']
            print(f"[OK] 使用现有数字人 ID: {dh_id}")
    else:
        print(f"[OK] 创建成功，数字人ID: {dh_id}")

    # 4. 测试对话
    if dh_id:
        test_chat(token, dh_id)

    print("\n\n[OK] 所有API测试完成！")

if __name__ == "__main__":
    main()
