import base64
import json
import os
import re
from collections.abc import Generator
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_INPUT_IMAGE_SIZE = 1024
IMAGE_SOURCE_KEYS = (
    "url",
    "download_url",
    "signed_url",
    "preview_url",
    "thumbnail_url",
    "remote_url",
    "file_url",
    "source_url",
    "href",
)
DIFY_INTERNAL_FILE_PATH_PREFIX = "/files/"
PLACEHOLDER_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2,}$")
COMMON_IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".svg",
)


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _preview_value(value: str, limit: int = 80) -> str:
    normalized = value.strip().replace("\n", " ")
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _looks_like_placeholder_reference(value: str) -> bool:
    normalized = value.strip()
    lower_normalized = normalized.lower()

    if normalized.startswith(("{{", "${")) or normalized.endswith("}}"):
        return True

    if "://" in normalized or normalized.startswith("data:image/"):
        return False

    if lower_normalized.endswith((".url", ".download_url", ".signed_url", ".preview_url")):
        return True

    return bool(
        PLACEHOLDER_REFERENCE_PATTERN.fullmatch(normalized)
        and not lower_normalized.endswith(COMMON_IMAGE_EXTENSIONS)
    )


def _resolve_dify_internal_url(relative_path: str) -> str | None:
    """尝试通过环境变量将 Dify 内部文件路径构造为完整 URL。
    优先使用 Docker 内部地址（INTERNAL_FILES_URL / DIFY_INNER_API_URL），
    确保 plugin_daemon 容器能通过 Docker 网络访问 API 服务。
    """
    for env_var in (
        "INTERNAL_FILES_URL",   # Dify 专为插件内部通信设置的地址
        "DIFY_INNER_API_URL",   # plugin_daemon 内置的内部 API 地址（默认 http://api:5001）
        "FILES_URL",            # 外部文件访问地址（可能不可达）
        "CONSOLE_API_URL",
        "SERVICE_API_URL",
    ):
        base = os.environ.get(env_var, "").strip().rstrip("/")
        if base and base.startswith(("http://", "https://")):
            return f"{base}{relative_path}"
    return None


def _try_read_dify_file_blob(file_obj) -> bytes | None:
    """尝试通过 Dify File 对象的 .blob 属性直接读取二进制内容。"""
    if isinstance(file_obj, (list, tuple)):
        for item in file_obj:
            result = _try_read_dify_file_blob(item)
            if result is not None:
                return result
        return None

    if isinstance(file_obj, (dict, str, int, float, bool, type(None))):
        return None

    try:
        blob_data = file_obj.blob
        if isinstance(blob_data, bytes) and len(blob_data) > 0:
            return blob_data
    except Exception:
        pass
    return None


def _detect_mime_type(data: bytes) -> str:
    """根据文件头魔数检测图片 MIME 类型。"""
    if data[:4] == b"\x89PNG":
        return "image/png"
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:3] == b"GIF":
        return "image/gif"
    return "image/jpeg"


def _validate_image_reference(image_reference: str, source_name: str) -> str:
    normalized = (image_reference or "").strip()
    if not normalized:
        raise ValueError(f"❌ {source_name} 为空，无法读取输入图像。")

    if normalized.startswith("data:image/"):
        return normalized

    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return normalized

    # 处理 Dify 内部文件路径（如 /files/{uuid}/file-preview?timestamp=...）
    if normalized.startswith(DIFY_INTERNAL_FILE_PATH_PREFIX):
        full_url = _resolve_dify_internal_url(normalized)
        if full_url:
            return full_url
        raise ValueError(
            f"❌ {source_name} 是 Dify 内部文件路径（{_preview_value(normalized)}），"
            "插件无法直接访问。请在 Dify 的 .env 文件中配置 FILES_URL 环境变量"
            "（如 FILES_URL=http://你的主机IP:端口），然后重启服务；"
            "或改用 input_image 文件参数传入图片。"
        )

    if _looks_like_placeholder_reference(normalized):
        raise ValueError(
            f"❌ {source_name} 看起来是变量引用或占位文本：{_preview_value(normalized)}。"
            "请优先传入 input_image 文件参数，或提供真实的公网 http(s) 图片 URL / data:image URL。"
        )

    raise ValueError(
        f"❌ {source_name} 仅支持公网 http(s) 图片 URL 或 data:image URL，"
        f"当前值不受支持：{_preview_value(normalized)}"
    )


def _iter_image_reference_candidates(value, path: str = "input_image", seen=None):
    if seen is None:
        seen = set()

    value_id = id(value)
    if value_id in seen:
        return
    seen.add(value_id)

    if isinstance(value, str):
        yield path, value
        return

    if isinstance(value, dict):
        image_url = value.get("image_url")
        if isinstance(image_url, dict):
            nested_url = image_url.get("url")
            if isinstance(nested_url, str):
                yield f"{path}.image_url.url", nested_url

        for key in IMAGE_SOURCE_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str):
                yield f"{path}.{key}", candidate

        for key, nested_value in value.items():
            if isinstance(nested_value, (dict, list, tuple)):
                yield from _iter_image_reference_candidates(
                    nested_value, f"{path}.{key}", seen
                )
        return

    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            if isinstance(item, (str, dict, list, tuple)):
                yield from _iter_image_reference_candidates(item, f"{path}[{index}]", seen)
        return

    # 处理 Dify File 等具有属性的对象（非 dict、str、list）
    if hasattr(value, "__dict__"):
        for key in IMAGE_SOURCE_KEYS:
            candidate = getattr(value, key, None)
            if isinstance(candidate, str):
                yield f"{path}.{key}", candidate


def _resolve_input_image_source(tool_parameters: dict) -> tuple[str | None, str | None]:
    input_image = tool_parameters.get("input_image")
    input_image_url = tool_parameters.get("input_image_url")

    if _has_value(input_image):
        # 优先尝试 Dify File 对象的 .blob 属性直接读取二进制内容
        blob_bytes = _try_read_dify_file_blob(input_image)
        if blob_bytes is not None:
            mime = _detect_mime_type(blob_bytes)
            b64 = base64.b64encode(blob_bytes).decode("utf-8")
            return f"data:{mime};base64,{b64}", "input_image"

        # .blob 不可用，回退到从字段中提取 URL
        seen_values = set()
        first_error = None

        for candidate_path, candidate_value in _iter_image_reference_candidates(input_image):
            if not isinstance(candidate_value, str):
                continue

            normalized_candidate = candidate_value.strip()
            if not normalized_candidate or normalized_candidate in seen_values:
                continue
            seen_values.add(normalized_candidate)

            try:
                return _validate_image_reference(normalized_candidate, candidate_path), "input_image"
            except ValueError as exc:
                if first_error is None:
                    first_error = exc

        if first_error is not None:
            raise first_error

        if isinstance(input_image, dict):
            available_keys = ", ".join(list(input_image.keys())[:8]) or "无"
            raise ValueError(
                "❌ input_image 文件对象中未找到可用的图片地址字段。"
                "请检查是否传入了包含 url、download_url、signed_url、preview_url 或 image_url.url 的文件对象。"
                f"当前顶层字段：{available_keys}"
            )

        raise ValueError(
            "❌ input_image 输入格式暂不支持。请传入 Dify 文件对象，或改用 input_image_url 提供真实的公网 URL / data:image URL。"
        )

    if isinstance(input_image_url, str) and input_image_url.strip():
        normalized_input_image_url = input_image_url.strip()
        if _looks_like_placeholder_reference(normalized_input_image_url):
            return None, None
        return _validate_image_reference(normalized_input_image_url, "input_image_url"), "input_image_url"

    return None, None


def _load_image_bytes(image_reference: str) -> bytes:
    if image_reference.startswith("data:image/"):
        try:
            _, base64_data = image_reference.split(",", 1)
            return base64.b64decode(base64_data)
        except Exception as exc:
            raise ValueError(f"无法解析 data:image 输入：{exc}") from exc

    response = requests.get(image_reference, timeout=30)
    response.raise_for_status()
    return response.content


def _normalize_input_image_to_data_url(image_reference: str) -> tuple[str, tuple[int, int], int]:
    image_bytes = _load_image_bytes(image_reference)
    image = Image.open(BytesIO(image_bytes))

    if max(image.size) > MAX_INPUT_IMAGE_SIZE:
        image.thumbnail((MAX_INPUT_IMAGE_SIZE, MAX_INPUT_IMAGE_SIZE), Image.Resampling.LANCZOS)

    if image.mode != "RGB":
        image = image.convert("RGB")

    output = BytesIO()
    image.save(output, format="JPEG", quality=85)
    jpeg_bytes = output.getvalue()
    data_url = f"data:image/jpeg;base64,{base64.b64encode(jpeg_bytes).decode('utf-8')}"
    return data_url, image.size, len(jpeg_bytes)


def _extract_image_reference(item: dict) -> str:
    if not isinstance(item, dict):
        return ""

    image_url = item.get("image_url")
    if isinstance(image_url, dict):
        url = image_url.get("url")
        if isinstance(url, str):
            return url.strip()

    if isinstance(image_url, str):
        return image_url.strip()

    url = item.get("url")
    if isinstance(url, str):
        return url.strip()

    return ""


def _extract_generated_images(message: dict) -> list[str]:
    images = []

    for image_item in message.get("images", []) or []:
        image_reference = _extract_image_reference(image_item)
        if image_reference:
            images.append(image_reference)

    if images:
        return images

    content = message.get("content")
    if isinstance(content, list):
        for content_item in content:
            if not isinstance(content_item, dict):
                continue
            if content_item.get("type") != "image_url":
                continue

            image_reference = _extract_image_reference(content_item)
            if image_reference:
                images.append(image_reference)

    return images


def _extract_message_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                text_parts.append(str(item.get("text")))
        return " ".join(text_parts).strip()

    return ""


def _image_reference_to_png_blob(image_reference: str) -> bytes:
    image_bytes = _load_image_bytes(image_reference)
    image = Image.open(BytesIO(image_bytes))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class Text2ImageTool(Tool):
    def _invoke(
        self, tool_parameters: dict
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        基于 OpenRouter API 的 Nano Banana 文生图工具

        Args:
            tool_parameters: 工具参数字典，包含 prompt、model、可选的 model_manual、input_image 和 input_image_url

        Yields:
            ToolInvokeMessage: 工具调用消息，包括进度反馈和最终图像结果
        """
        api_key = self.runtime.credentials.get("api_key")

        prompt = tool_parameters.get("prompt", "")
        if not prompt:
            yield self.create_text_message("❌ 请输入图像生成提示词")
            return

        model_manual = (tool_parameters.get("model_manual") or "").strip()
        selected_model = (tool_parameters.get("model") or "").strip()
        model = model_manual or selected_model or DEFAULT_MODEL

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            raw_input_image = tool_parameters.get("input_image")
            raw_input_image_url = tool_parameters.get("input_image_url")
            normalized_input_image_url = (
                raw_input_image_url.strip()
                if isinstance(raw_input_image_url, str)
                else ""
            )
            input_image_reference, input_source_name = _resolve_input_image_source(tool_parameters)
            ignored_placeholder_input_image_url = (
                not _has_value(raw_input_image)
                and bool(normalized_input_image_url)
                and _looks_like_placeholder_reference(normalized_input_image_url)
                and input_image_reference is None
            )

            yield self.create_text_message(f"🔍 调试信息 - 使用模型: {model}")
            if input_source_name == "input_image" and input_image_reference and input_image_reference.startswith("data:image/"):
                yield self.create_text_message("🔍 调试信息 - 通过 File.blob 或 data URL 直接读取了输入图像")
            elif _has_value(raw_input_image):
                yield self.create_text_message("🔍 调试信息 - 检测到 input_image 文件输入")
            elif input_source_name == "input_image_url":
                yield self.create_text_message("🔍 调试信息 - 检测到 input_image_url 字符串输入")
            elif ignored_placeholder_input_image_url:
                yield self.create_text_message("🔍 调试信息 - input_image_url 为占位值，已按未传图片处理")

            yield self.create_text_message("🍌 Nano Banana 正在启动图像生成...")
            yield self.create_text_message("🚀 正在连接 OpenRouter API...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(
                f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
            )

            content = [{"type": "text", "text": prompt}]
            if input_image_reference:
                yield self.create_text_message(f"🖼️ 输入图像来源: {input_source_name}")
                yield self.create_text_message("🔍 正在处理输入图像...")

                try:
                    data_url, image_size, image_bytes_size = _normalize_input_image_to_data_url(
                        input_image_reference
                    )
                except Exception as exc:
                    yield self.create_text_message(f"❌ 输入图像处理失败: {exc}")
                    yield self.create_text_message(
                        "💡 请确认传入的是 input_image 文件对象，或真实可访问的公网图片 URL / data:image URL。"
                    )
                    return

                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    }
                )
                yield self.create_text_message(f"✅ 输入图像处理完成，尺寸: {image_size}")
                yield self.create_text_message(f"📊 输入图像大小: {image_bytes_size} 字节")
                yield self.create_text_message("🔄 将进行图像到图像转换...")

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            }

            yield self.create_text_message("⏳ 正在生成图像，请稍候...")
            yield self.create_text_message("🎨 AI 正在发挥创意...")

            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=60,
            )

            if response.status_code != 200:
                yield self.create_text_message(f"🔧 API 响应状态码: {response.status_code}")
                yield self.create_text_message(f"🔧 响应内容: {response.text[:300]}")

            response.raise_for_status()
            response_data = response.json()

            choices = response_data.get("choices", [])
            if not choices:
                yield self.create_text_message("❌ API 响应中没有找到生成结果")
                return

            message = choices[0].get("message", {})
            generated_images = _extract_generated_images(message)

            if not generated_images:
                yield self.create_text_message("❌ 没有生成图像数据")
                message_text = _extract_message_text(message)
                if message_text:
                    yield self.create_text_message(f"📝 模型响应: {message_text}")
                return

            yield self.create_text_message(f"🎉 成功生成 {len(generated_images)} 张图像！")

            for index, image_reference in enumerate(generated_images, start=1):
                yield self.create_text_message(f"🎨 正在处理第 {index} 张图像...")
                try:
                    image_blob = _image_reference_to_png_blob(image_reference)
                except Exception as exc:
                    yield self.create_text_message(f"❌ 处理第 {index} 张图像时出错: {exc}")
                    continue

                yield self.create_blob_message(
                    blob=image_blob,
                    meta={"mime_type": "image/png"},
                )
                yield self.create_text_message(f"✅ 第 {index} 张图像处理完成！")
                yield self.create_text_message(f"📊 图像大小: {len(image_blob)} 字节")

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

        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 401:
                yield self.create_text_message("❌ OpenRouter API Key 无效，请检查您的 API Key")
                yield self.create_text_message("💡 请前往 https://openrouter.ai/keys 获取有效的 API Key")
            elif exc.response.status_code == 402:
                yield self.create_text_message("❌ OpenRouter 账户余额不足")
                yield self.create_text_message("💡 请前往 https://openrouter.ai/credits 充值")
            elif exc.response.status_code == 429:
                yield self.create_text_message("❌ API 调用频率过高，请稍后再试")
                yield self.create_text_message("💡 建议等待几分钟后重试")
            elif exc.response.status_code == 500:
                yield self.create_text_message("❌ OpenRouter 服务器内部错误")
                yield self.create_text_message("💡 可能的解决方案:")
                yield self.create_text_message("1. 检查提示词是否包含敏感内容")
                yield self.create_text_message("2. 尝试更换模型")
                yield self.create_text_message("3. 稍后重试")
            else:
                yield self.create_text_message(f"❌ HTTP 错误: {exc.response.status_code}")
                if hasattr(exc.response, "text"):
                    yield self.create_text_message(f"🔧 错误详情: {exc.response.text[:200]}")

        except requests.exceptions.Timeout:
            yield self.create_text_message("❌ 请求超时，请检查网络连接或稍后重试")
            yield self.create_text_message("💡 建议检查网络连接状态")

        except requests.exceptions.RequestException as exc:
            yield self.create_text_message(f"❌ 网络请求错误: {exc}")
            yield self.create_text_message("💡 请检查网络连接是否正常")

        except json.JSONDecodeError as exc:
            yield self.create_text_message(f"❌ API 响应解析错误: {exc}")
            yield self.create_text_message("🔧 这可能是 OpenRouter API 返回了非 JSON 格式的响应")

        except KeyError as exc:
            yield self.create_text_message(f"❌ API 响应格式错误，缺少字段: {exc}")

        except ValueError as exc:
            yield self.create_text_message(str(exc))

        except Exception as exc:
            yield self.create_text_message(f"❌ 生成图像时出现未知错误: {exc}")
            yield self.create_text_message("🔧 请联系技术支持或查看详细日志")
            import traceback

            yield self.create_text_message(f"🔧 调试信息: {traceback.format_exc()}")
