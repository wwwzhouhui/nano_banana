#!/usr/bin/env python3
"""
Nano Banana OpenRouter API 连接测试
测试 API 连接和基本认证状态
"""

import os

import requests


def test_openrouter_connection():
    """测试 OpenRouter API 连接"""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 OPENROUTER_API_KEY")
        print("   export OPENROUTER_API_KEY=sk-or-v1-your-api-key")
        return False

    print("🍌 Nano Banana - 测试 OpenRouter API 连接...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={},
            timeout=60,
        )

        print(f"📊 响应状态码: {response.status_code}")
        print(f"📝 响应内容: {response.text[:300]}")

        if response.status_code == 400:
            print("✅ API Key 有效，OpenRouter 连接正常")
            print("💡 400 是预期结果，因为这里只做最小校验请求，没有传 model/messages")
            return True

        if response.status_code == 200:
            print("✅ API 连接成功")
            return True

        if response.status_code == 401:
            print("❌ API Key 无效或已过期")
            return False

        print(f"❌ API 调用失败: {response.status_code}")
        return False

    except Exception as e:
        print(f"❌ 连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_openrouter_connection()
    if success:
        print("🎉 OpenRouter API 测试通过")
    else:
        print("💡 请检查 API Key 和网络连接")
