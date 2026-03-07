#!/usr/bin/env python3
"""
Nano Banana OpenRouter 文生图工具测试
"""

import base64
import json
import os
import sys
from io import BytesIO
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from PIL import Image

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _install_dify_plugin_stubs():
    dify_plugin_module = ModuleType("dify_plugin")
    entities_module = ModuleType("dify_plugin.entities")
    tool_module = ModuleType("dify_plugin.entities.tool")

    class Tool:
        def create_text_message(self, message):
            return SimpleNamespace(type="text", message=message)

        def create_blob_message(self, blob, meta):
            return SimpleNamespace(type="blob", blob=blob, meta=meta)

    class ToolInvokeMessage:
        pass

    dify_plugin_module.Tool = Tool
    tool_module.ToolInvokeMessage = ToolInvokeMessage

    sys.modules.setdefault("dify_plugin", dify_plugin_module)
    sys.modules.setdefault("dify_plugin.entities", entities_module)
    sys.modules.setdefault("dify_plugin.entities.tool", tool_module)


_install_dify_plugin_stubs()

from tools.text2image import DEFAULT_MODEL, Text2ImageTool


def _create_png_bytes(color=(255, 0, 0)) -> bytes:
    image = Image.new("RGB", (2, 2), color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


TEST_IMAGE_BYTES = _create_png_bytes()
TEST_IMAGE_BASE64 = base64.b64encode(TEST_IMAGE_BYTES).decode("utf-8")


class MockRuntime:
    """模拟运行时环境"""

    def __init__(self, api_key: str):
        self.credentials = {"api_key": api_key}


class MockJsonResponse:
    """模拟 OpenRouter JSON 响应"""

    def __init__(self, payload: dict, status_code: int = 200):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class MockBinaryResponse:
    """模拟二进制图像响应"""

    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        self.text = ""

    def raise_for_status(self):
        return None


def _mock_success_response_with_images() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": "ok",
                    "images": [
                        {
                            "image_url": {
                                "url": f"data:image/png;base64,{TEST_IMAGE_BASE64}"
                            }
                        }
                    ],
                }
            }
        ]
    }


def _mock_success_response_with_content_segments() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "ok"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{TEST_IMAGE_BASE64}"
                            },
                        },
                    ]
                }
            }
        ]
    }


def _unexpected_get(*args, **kwargs):
    raise AssertionError("requests.get should not be called in this test")


def _invoke_tool(
    params: dict,
    response_payload: dict | None = None,
    get_side_effect=None,
):
    tool = Text2ImageTool()
    tool.runtime = MockRuntime("sk-or-v1-test-key")
    captured_payload: dict = {}

    def mock_post(url, headers=None, data=None, timeout=None):
        captured_payload.update(json.loads(data))
        return MockJsonResponse(response_payload or _mock_success_response_with_images())

    with patch("tools.text2image.requests.post", side_effect=mock_post) as mock_post_fn:
        with patch(
            "tools.text2image.requests.get",
            side_effect=get_side_effect or _unexpected_get,
        ) as mock_get_fn:
            messages = list(tool._invoke(params))

    return messages, captured_payload, mock_post_fn, mock_get_fn


def _text_messages(messages):
    return [message.message for message in messages if message.type == "text"]


def _blob_messages(messages):
    return [message for message in messages if message.type == "blob"]


def test_default_model_used_when_model_is_missing():
    _, payload, _, _ = _invoke_tool(
        {
            "prompt": "一根放在白色背景前的香蕉，简洁产品摄影风格",
        }
    )
    assert payload["model"] == DEFAULT_MODEL


def test_selected_model_used_when_manual_model_is_missing():
    _, payload, _, _ = _invoke_tool(
        {
            "prompt": "一根未来感香蕉，霓虹色灯光",
            "model": "google/gemini-3-pro-image-preview",
        }
    )
    assert payload["model"] == "google/gemini-3-pro-image-preview"


def test_manual_model_overrides_selected_model():
    _, payload, _, _ = _invoke_tool(
        {
            "prompt": "一根像艺术雕塑一样的香蕉",
            "model": "google/gemini-3-pro-image-preview",
            "model_manual": "openrouter/custom-image-model",
        }
    )
    assert payload["model"] == "openrouter/custom-image-model"


def test_text_only_generation_builds_text_only_request_content():
    _, payload, _, mock_get = _invoke_tool(
        {
            "prompt": "一根漂浮在极简展台上的香蕉",
        }
    )
    assert payload["messages"][0]["content"] == [
        {
            "type": "text",
            "text": "一根漂浮在极简展台上的香蕉",
        }
    ]
    assert mock_get.call_count == 0


def test_input_image_file_takes_priority_over_input_image_url():
    def mock_get(url, timeout=None):
        assert url == "https://files.example.com/source.png"
        return MockBinaryResponse(TEST_IMAGE_BYTES)

    messages, payload, _, mock_get_fn = _invoke_tool(
        {
            "prompt": "把这张图片做成手办效果",
            "input_image": {
                "url": "https://files.example.com/source.png",
                "mime_type": "image/png",
            },
            "input_image_url": "https://fallback.example.com/ignored.png",
        },
        get_side_effect=mock_get,
    )

    content = payload["messages"][0]["content"]
    assert len(content) == 2
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert mock_get_fn.call_count == 1
    assert any("输入图像来源: input_image" in message for message in _text_messages(messages))


def test_placeholder_input_image_url_is_ignored_for_prompt_only_generation():
    messages, payload, mock_post_fn, mock_get_fn = _invoke_tool(
        {
            "prompt": "把这张图片做成 PVC 手办",
            "input_image_url": "1756601479774.picture.url",
        }
    )

    text_messages = _text_messages(messages)
    assert mock_post_fn.call_count == 1
    assert mock_get_fn.call_count == 0
    assert payload["messages"][0]["content"] == [
        {
            "type": "text",
            "text": "把这张图片做成 PVC 手办",
        }
    ]
    assert any("input_image_url 为占位值" in message for message in text_messages)
    assert not any("变量引用或占位文本" in message for message in text_messages)


def test_openrouter_message_images_data_url_outputs_blob():
    messages, _, _, _ = _invoke_tool(
        {
            "prompt": "生成一个可爱的香蕉角色",
        },
        response_payload=_mock_success_response_with_images(),
    )

    blobs = _blob_messages(messages)
    assert len(blobs) == 1
    assert blobs[0].meta == {"mime_type": "image/png"}
    assert blobs[0].blob.startswith(b"\x89PNG")


def test_openrouter_message_content_segments_output_blob():
    messages, _, _, _ = _invoke_tool(
        {
            "prompt": "生成一个香蕉主题玩具包装",
        },
        response_payload=_mock_success_response_with_content_segments(),
    )

    blobs = _blob_messages(messages)
    assert len(blobs) == 1
    assert blobs[0].meta == {"mime_type": "image/png"}
    assert blobs[0].blob.startswith(b"\x89PNG")


def main():
    """主函数"""
    test_cases = [
        ("默认模型回退测试", test_default_model_used_when_model_is_missing),
        ("下拉模型选择测试", test_selected_model_used_when_manual_model_is_missing),
        ("手工模型覆盖测试", test_manual_model_overrides_selected_model),
        ("纯文生图请求结构测试", test_text_only_generation_builds_text_only_request_content),
        ("文件输入优先级测试", test_input_image_file_takes_priority_over_input_image_url),
        ("占位字符串忽略测试", test_placeholder_input_image_url_is_ignored_for_prompt_only_generation),
        ("message.images 输出解析测试", test_openrouter_message_images_data_url_outputs_blob),
        ("message.content 分段输出解析测试", test_openrouter_message_content_segments_output_blob),
    ]

    print("🍌 Nano Banana 文生图工具测试")
    print("=" * 60)

    for name, test_func in test_cases:
        try:
            test_func()
            print(f"✅ {name} 通过")
        except AssertionError as exc:
            print(f"❌ {name} 失败: {exc}")
            raise

    print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    main()
