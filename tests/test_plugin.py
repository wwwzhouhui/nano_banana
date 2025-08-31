#!/usr/bin/env python3
"""
Nano Banana OpenRouter 文生图插件集成测试
"""

import os
import sys
import time
from tools.text2image import Text2ImageTool

class MockRuntime:
    """模拟运行时环境"""
    def __init__(self, api_key: str):
        self.credentials = {"api_key": api_key}

def test_nano_banana_plugin():
    """测试 Nano Banana 文生图插件功能"""
    
    # 从环境变量获取 API Key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 OPENROUTER_API_KEY")
        print("   export OPENROUTER_API_KEY=sk-or-v1-your-api-key")
        return False
    
    print("🍌 开始测试 Nano Banana OpenRouter 文生图插件...")
    print(f"🔑 使用 API Key: {api_key[:20]}...")
    
    # 创建工具实例
    tool = Text2ImageTool()
    tool.runtime = MockRuntime(api_key)
    
    # 测试参数
    test_cases = [
        {
            "name": "基础香蕉主题测试",
            "params": {
                "prompt": "一根金黄色的香蕉放在木质桌面上，阳光透过窗户洒在上面，温暖的光线",
                "model": "google/gemini-2.5-flash-image-preview:free"
            }
        },
        {
            "name": "创意场景测试",
            "params": {
                "prompt": "未来科技风格的香蕉机器人在霓虹灯城市中行走，赛博朋克风格，高质量渲染",
                "model": "google/gemini-2.5-flash-image-preview:free"
            }
        },
        {
            "name": "艺术风格测试",
            "params": {
                "prompt": "梵高风格的香蕉静物画，油画质感，色彩丰富，艺术感强烈",
                "model": "google/gemini-2.5-flash-image-preview:free"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 执行测试: {test_case['name']}")
        print(f"🎨 提示词: {test_case['params']['prompt']}")
        print("=" * 80)
        
        try:
            start_time = time.time()
            
            # 调用工具
            messages = list(tool._invoke(test_case['params']))
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 分析结果
            image_generated = False
            error_occurred = False
            
            for i, message in enumerate(messages, 1):
                if hasattr(message, 'type'):
                    if message.type == 'text':
                        print(f"[{i}] 📄 {message.message}")
                        if "错误" in message.message or "失败" in message.message:
                            error_occurred = True
                    elif message.type == 'blob':
                        print(f"[{i}] 🖼️ 图像生成成功！")
                        print(f"     📊 图像大小: {len(message.blob)} 字节")
                        print(f"     📋 MIME 类型: {message.meta.get('mime_type', 'unknown')}")
                        image_generated = True
                        
                        # 保存测试图像
                        filename = f"nano_banana_{test_case['name'].replace(' ', '_').replace('测试', '')}.png"
                        with open(filename, 'wb') as f:
                            f.write(message.blob)
                        print(f"     💾 图像已保存为: {filename}")
                else:
                    print(f"[{i}] ❓ 未知消息类型: {message}")
            
            print(f"\n⏱️ 测试耗时: {duration:.2f} 秒")
            
            if image_generated and not error_occurred:
                print(f"✅ {test_case['name']} 测试成功")
            else:
                print(f"❌ {test_case['name']} 测试失败")
                return False
                
        except Exception as e:
            print(f"❌ {test_case['name']} 测试异常: {str(e)}")
            return False
        
        # 测试间隔，避免API频率限制
        if test_case != test_cases[-1]:  # 不是最后一个测试
            print("⏳ 等待 3 秒避免API频率限制...")
            time.sleep(3)
    
    return True

def main():
    """主函数"""
    print("🍌 Nano Banana OpenRouter 文生图插件测试工具")
    print("=" * 80)
    
    # 检查依赖
    try:
        import requests
        import PIL
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 运行测试
    success = test_nano_banana_plugin()
    
    if success:
        print("\n🎉 所有测试通过！Nano Banana 插件可以正常使用。")
        print("\n📋 下一步:")
        print("1. 将插件部署到 Dify 环境")
        print("2. 在 Dify 中配置 OpenRouter API Key")
        print("3. 在工作流中使用 Nano Banana 文生图工具")
        print("4. 享受高质量的AI图像生成服务！")
    else:
        print("\n💡 故障排除建议:")
        print("1. 检查网络连接是否正常")
        print("2. 验证 OpenRouter API Key 是否有效")
        print("3. 确认账户余额是否充足")
        print("4. 查看详细错误信息进行调试")
        print("5. 联系 Nano Banana 技术支持")

if __name__ == "__main__":
    main()