"""
MindPal Backend V2 - API 测试脚本
运行: python -m scripts.test_api
"""

import asyncio
import httpx
from typing import Optional

# 配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 测试账号
TEST_PHONE = "13800000000"
TEST_PASSWORD = "test123456"


class APITester:
    """API测试器"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token: Optional[str] = None

    async def close(self):
        await self.client.aclose()

    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    async def test_health(self):
        """测试健康检查"""
        print("\n📍 测试健康检查...")
        resp = await self.client.get(f"{BASE_URL}/health")
        print(f"   状态: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        return resp.status_code == 200

    async def test_login(self):
        """测试登录"""
        print("\n📍 测试登录...")
        resp = await self.client.post(
            f"{API_URL}/auth/login",
            json={"phone": TEST_PHONE, "password": TEST_PASSWORD}
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        print(f"   响应: {data}")

        if resp.status_code == 200 and data.get("code") == 0:
            self.token = data["data"]["access_token"]
            print(f"   ✅ 获取Token成功")
            return True
        return False

    async def test_player_profile(self):
        """测试获取角色信息"""
        print("\n📍 测试获取角色信息...")
        resp = await self.client.get(
            f"{API_URL}/player/profile",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        return resp.status_code == 200

    async def test_dialogue(self):
        """测试AI对话"""
        print("\n📍 测试AI对话...")
        resp = await self.client.post(
            f"{API_URL}/dialogue/chat",
            headers=self._headers(),
            json={
                "npc_id": "bei",
                "message": "你好，小贝！",
            }
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        if resp.status_code == 200:
            print(f"   AI回复: {data.get('data', {}).get('reply', '')[:100]}...")
        else:
            print(f"   响应: {data}")
        return resp.status_code == 200

    async def test_inventory(self):
        """测试背包"""
        print("\n📍 测试背包...")
        resp = await self.client.get(
            f"{API_URL}/inventory",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        return resp.status_code == 200

    async def test_shop(self):
        """测试商城"""
        print("\n📍 测试商城...")
        resp = await self.client.get(
            f"{API_URL}/shop/items",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        items = data.get("data", [])
        print(f"   商品数量: {len(items)}")
        return resp.status_code == 200

    async def test_quests(self):
        """测试任务"""
        print("\n📍 测试任务列表...")
        resp = await self.client.get(
            f"{API_URL}/quests",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        quests = data.get("data", [])
        print(f"   任务数量: {len(quests)}")
        return resp.status_code == 200

    async def test_achievements(self):
        """测试成就"""
        print("\n📍 测试成就列表...")
        resp = await self.client.get(
            f"{API_URL}/achievements",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        achievements = data.get("data", [])
        print(f"   成就数量: {len(achievements)}")
        return resp.status_code == 200

    async def test_recharge_products(self):
        """测试充值商品"""
        print("\n📍 测试充值商品...")
        resp = await self.client.get(
            f"{API_URL}/payment/products",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        products = data.get("data", [])
        print(f"   商品数量: {len(products)}")
        for p in products[:3]:
            print(f"      - {p.get('name')}: ¥{p.get('price')}")
        return resp.status_code == 200

    async def test_add_diamonds(self):
        """测试添加钻石"""
        print("\n📍 测试添加钻石...")
        resp = await self.client.post(
            f"{API_URL}/payment/test/add-diamonds?amount=500",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        return resp.status_code == 200

    async def test_voice_list(self):
        """测试语音列表"""
        print("\n📍 测试语音列表...")
        resp = await self.client.get(
            f"{API_URL}/voice/voices",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        data = resp.json()
        voices = data.get("data", [])
        print(f"   可用语音: {len(voices)}")
        return resp.status_code == 200

    async def test_three_keys_status(self):
        """测试三钥匙状态"""
        print("\n📍 测试三钥匙挑战状态...")
        resp = await self.client.get(
            f"{API_URL}/three-keys/status",
            headers=self._headers()
        )
        print(f"   状态: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        return resp.status_code == 200


async def main():
    """主测试函数"""
    print("=" * 60)
    print("MindPal Backend V2 - API 测试")
    print("=" * 60)

    tester = APITester()
    results = {}

    try:
        # 基础测试
        results["健康检查"] = await tester.test_health()
        results["登录"] = await tester.test_login()

        if not results["登录"]:
            print("\n❌ 登录失败，无法继续测试")
            return

        # 需要认证的测试
        results["角色信息"] = await tester.test_player_profile()
        results["AI对话"] = await tester.test_dialogue()
        results["背包"] = await tester.test_inventory()
        results["商城"] = await tester.test_shop()
        results["任务"] = await tester.test_quests()
        results["成就"] = await tester.test_achievements()
        results["充值商品"] = await tester.test_recharge_products()
        results["添加钻石"] = await tester.test_add_diamonds()
        results["语音列表"] = await tester.test_voice_list()
        results["三钥匙"] = await tester.test_three_keys_status()

    except httpx.ConnectError:
        print("\n❌ 无法连接到服务器，请确保后端已启动")
        print("   运行: uvicorn app.main:app --reload")
        return

    finally:
        await tester.close()

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n   通过: {passed}/{len(results)}")
    if failed > 0:
        print(f"   失败: {failed}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
