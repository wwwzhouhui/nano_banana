import requests
import json
import base64
from collections.abc import Generator
from PIL import Image
from io import BytesIO
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool

class Text2ImageTool(Tool):
    def _invoke(
        self, tool_parameters: dict
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        基于 OpenRouter API 的 Nano Banana 文生图工具
        完全基于 zz.py 的实现逻辑
        
        Args:
            tool_parameters: 工具参数字典，包含 prompt、model 和可选的 input_image_url
            
        Yields:
            ToolInvokeMessage: 工具调用消息，包括进度反馈和最终图像结果
        """
        # 1. 获取 API 配置
        api_key = self.runtime.credentials.get("api_key")
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # 2. 获取和验证参数
        prompt = tool_parameters.get("prompt", "")
        if not prompt:
            yield self.create_text_message("❌ 请输入图像生成提示词")
            return
            
        model = tool_parameters.get("model", "google/gemini-2.5-flash-image-preview:free")
        input_image_url = tool_parameters.get("input_image_url", "")
        
        # 3. 构建请求头（完全按照 zz.py 的格式）
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            yield self.create_text_message("🍌 Nano Banana 正在启动图像生成...")
            yield self.create_text_message("🚀 正在连接 OpenRouter API...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # 4. 构建消息内容（基于 zz.py 的结构）
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # 如果有输入图像，添加到内容中
            if input_image_url:
                yield self.create_text_message(f"🖼️ 输入图像: {input_image_url}")
                yield self.create_text_message("🔍 正在处理输入图像...")
                
                try:
                    # 下载图像并转换为base64格式
                    yield self.create_text_message("📥 正在下载图像...")
                    img_response = requests.get(input_image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # 验证图像数据
                    image = Image.open(BytesIO(img_response.content))
                    yield self.create_text_message(f"✅ 图像下载成功，尺寸: {image.size}")
                    
                    # 检查图像大小，如果太大则压缩
                    max_size = 1024  # 最大尺寸
                    if max(image.size) > max_size:
                        yield self.create_text_message(f"🔧 图像过大，正在压缩到 {max_size}px...")
                        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        yield self.create_text_message(f"✅ 压缩完成，新尺寸: {image.size}")
                    
                    # 转换为RGB格式（确保兼容性）
                    if image.mode != 'RGB':
                        yield self.create_text_message(f"🔧 转换图像格式: {image.mode} -> RGB")
                        image = image.convert('RGB')
                    
                    # 转换为base64格式
                    yield self.create_text_message("🔄 正在转换为base64格式...")
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format='JPEG', quality=85)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # 编码为base64
                    img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
                    data_url = f"data:image/jpeg;base64,{img_base64}"
                    
                    yield self.create_text_message(f"✅ 图像处理完成，大小: {len(img_byte_arr)} 字节")
                    
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    })
                    yield self.create_text_message("🔄 将进行图像到图像转换...")
                    
                except Exception as e:
                    yield self.create_text_message(f"❌ 图像处理失败: {str(e)}")
                    yield self.create_text_message("💡 建议:")
                    yield self.create_text_message("1. 检查图像URL是否正确")
                    yield self.create_text_message("2. 确保图像格式为 JPG/PNG/WebP")
                    yield self.create_text_message("3. 尝试使用其他图像URL")
                    return
            
            # 5. 构建请求载荷（完全按照 zz.py 的格式）
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            
            yield self.create_text_message("⏳ 正在生成图像，请稍候...")
            yield self.create_text_message("🎨 AI 正在发挥创意...")
            
            # 6. 发送请求（完全按照 zz.py 的方式）
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),  # 使用 data 参数，与 zz.py 保持一致
                timeout=60
            )
            
            # 7. 检查响应状态
            if response.status_code != 200:
                yield self.create_text_message(f"🔧 API 响应状态码: {response.status_code}")
                yield self.create_text_message(f"🔧 响应内容: {response.text[:300]}")
            
            response.raise_for_status()
            
            # 8. 解析响应数据（按照 zz.py 的响应格式）
            response_data = response.json()
            
            # 检查响应结构
            choices = response_data.get("choices", [])
            if not choices:
                yield self.create_text_message("❌ API 响应中没有找到生成结果")
                return
            
            message = choices[0].get("message", {})
            images = message.get("images", [])
            
            if not images:
                yield self.create_text_message("❌ 没有生成图像数据")
                # 输出描述文本（如果有）
                content = message.get("content", "")
                if content:
                    yield self.create_text_message(f"📝 模型响应: {content}")
                return
            
            yield self.create_text_message(f"🎉 成功生成 {len(images)} 张图像！")
            
            # 9. 处理生成的图像（按照 zz.py 的响应格式）
            for i, image_data in enumerate(images):
                image_url = image_data.get("image_url", {}).get("url", "")
                
                if not image_url:
                    yield self.create_text_message(f"❌ 第 {i+1} 张图像数据无效")
                    continue
                
                # 检查是否是 Base64 格式（data:image/png;base64,xxx）
                if image_url.startswith("data:image/"):
                    yield self.create_text_message(f"🎨 正在处理第 {i+1} 张图像...")
                    
                    # 提取 Base64 数据
                    try:
                        # 分离 MIME 类型和 Base64 数据
                        header, base64_data = image_url.split(",", 1)
                        
                        # 解码 Base64 数据
                        image_bytes = base64.b64decode(base64_data)
                        
                        # 验证图像数据
                        image = Image.open(BytesIO(image_bytes))
                        
                        # 转换为 PNG 格式（统一格式）
                        img_byte_arr = BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # 返回图像
                        yield self.create_blob_message(
                            blob=img_byte_arr,
                            meta={"mime_type": "image/png"}
                        )
                        
                        yield self.create_text_message(f"✅ 第 {i+1} 张图像生成完成！")
                        yield self.create_text_message(f"📊 图像大小: {len(img_byte_arr)} 字节")
                        
                    except Exception as e:
                        yield self.create_text_message(f"❌ 处理第 {i+1} 张图像时出错: {str(e)}")
                        continue
                        
                else:
                    # 如果是 URL 格式，下载图像
                    yield self.create_text_message(f"🌐 正在下载第 {i+1} 张图像...")
                    try:
                        img_response = requests.get(image_url, timeout=30)
                        img_response.raise_for_status()
                        
                        # 验证图像数据
                        image = Image.open(BytesIO(img_response.content))
                        
                        # 转换为 PNG 格式
                        img_byte_arr = BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # 返回图像
                        yield self.create_blob_message(
                            blob=img_byte_arr,
                            meta={"mime_type": "image/png"}
                        )
                        
                        yield self.create_text_message(f"✅ 第 {i+1} 张图像下载完成！")
                        yield self.create_text_message(f"📊 图像大小: {len(img_byte_arr)} 字节")
                        
                    except Exception as e:
                        yield self.create_text_message(f"❌ 下载第 {i+1} 张图像时出错: {str(e)}")
                        continue
            
            # 10. 输出使用统计信息（如果有）
            usage = response_data.get("usage", {})
            if usage:
                total_tokens = usage.get("total_tokens", 0)
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                yield self.create_text_message(
                    f"📊 Token 使用统计: 总计 {total_tokens} (提示 {prompt_tokens} + 完成 {completion_tokens})"
                )
            
            yield self.create_text_message("🍌 Nano Banana 图像生成任务完成！")
            yield self.create_text_message("🎉 感谢使用 Nano Banana 文生图服务！")
        
        except requests.exceptions.HTTPError as e:
            # HTTP 错误处理（基于 OpenRouter 的错误码）
            if e.response.status_code == 401:
                yield self.create_text_message("❌ OpenRouter API Key 无效，请检查您的 API Key")
                yield self.create_text_message("💡 请前往 https://openrouter.ai/keys 获取有效的 API Key")
            elif e.response.status_code == 402:
                yield self.create_text_message("❌ OpenRouter 账户余额不足")
                yield self.create_text_message("💡 请前往 https://openrouter.ai/credits 充值")
            elif e.response.status_code == 429:
                yield self.create_text_message("❌ API 调用频率过高，请稍后再试")
                yield self.create_text_message("💡 建议等待几分钟后重试")
            elif e.response.status_code == 500:
                yield self.create_text_message("❌ OpenRouter 服务器内部错误")
                yield self.create_text_message("💡 可能的解决方案:")
                yield self.create_text_message("1. 检查提示词是否包含敏感内容")
                yield self.create_text_message("2. 尝试更换模型")
                yield self.create_text_message("3. 稍后重试")
            else:
                yield self.create_text_message(f"❌ HTTP 错误: {e.response.status_code}")
                if hasattr(e.response, 'text'):
                    yield self.create_text_message(f"🔧 错误详情: {e.response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            yield self.create_text_message("❌ 请求超时，请检查网络连接或稍后重试")
            yield self.create_text_message("💡 建议检查网络连接状态")
            
        except requests.exceptions.RequestException as e:
            yield self.create_text_message(f"❌ 网络请求错误: {str(e)}")
            yield self.create_text_message("💡 请检查网络连接是否正常")
            
        except json.JSONDecodeError as e:
            yield self.create_text_message(f"❌ API 响应解析错误: {str(e)}")
            yield self.create_text_message("🔧 这可能是 OpenRouter API 返回了非 JSON 格式的响应")
            
        except KeyError as e:
            yield self.create_text_message(f"❌ API 响应格式错误，缺少字段: {str(e)}")
            
        except Exception as e:
            yield self.create_text_message(f"❌ 生成图像时出现未知错误: {str(e)}")
            yield self.create_text_message("🔧 请联系技术支持或查看详细日志")
            # 在开发环境中可以添加详细的错误信息
            import traceback
            yield self.create_text_message(f"🔧 调试信息: {traceback.format_exc()}")