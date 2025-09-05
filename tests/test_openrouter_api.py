#!/usr/bin/env python3
"""
Nano Banana OpenRouter API 连接测试
测试 API 连接和基本功能
"""

import os
import requests
import json
from unittest.mock import Mock

def test_openrouter_connection():
    """测试 OpenRouter API 连接"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 OPENROUTER_API_KEY")
        print("   export OPENROUTER_API_KEY=sk-or-v1-your-api-key")
        return False
    
    print("🍌 Nano Banana - 测试 OpenRouter API 连接...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 简单的测试请求
    payload = {
        "model": "deepseek/deepseek-chat-v3.1:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "生成一个简单的黄色香蕉图像"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 连接成功")
            
            # 检查响应结构
            if "choices" in data and data["choices"]:
                message = data["choices"][0].get("message", {})
                images = message.get("images", [])
                
                if images:
                    print(f"🎨 成功生成 {len(images)} 张图像")
                    print("🍌 Nano Banana API 测试通过！")
                    return True
                else:
                    print("⚠️ API 响应正常但未生成图像")
                    return False
            else:
                print("⚠️ API 响应格式异常")
                return False
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
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