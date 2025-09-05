from typing import Any
import requests
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin import ToolProvider

class NanaBananaProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        验证 OpenRouter API 凭据有效性
        
        Args:
            credentials: 包含 OpenRouter API key 的字典
            
        Raises:
            ToolProviderCredentialValidationError: 当凭据验证失败时
        """
        try:
            # 1. 检查 API key 是否存在
            api_key = credentials.get("api_key")
            if not api_key:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter API key 不能为空"
                )
            
            # 2. 检查 API key 格式
            if not api_key.startswith("sk-or-v1-"):
                raise ToolProviderCredentialValidationError(
                    "无效的 OpenRouter API key 格式。应该以 'sk-or-v1-' 开头"
                )
            
            # 3. 检查 API key 长度
            if len(api_key) < 20:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter API key 长度不正确"
                )
            
            # 4. 发送测试请求验证 API key 有效性
            self._test_openrouter_connection(api_key)
            
        except ToolProviderCredentialValidationError:
            # 重新抛出已知的验证错误
            raise
        except Exception as e:
            raise ToolProviderCredentialValidationError(
                f"OpenRouter API 凭据验证失败: {str(e)}"
            )
    
    def _test_openrouter_connection(self, api_key: str) -> None:
        """
        测试 OpenRouter API 连接有效性
        
        Args:
            api_key: OpenRouter API key
            
        Raises:
            ToolProviderCredentialValidationError: 当 API 连接测试失败时
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 使用一个更通用的模型进行测试，避免404错误
            test_payload = {
                "model": "deepseek/deepseek-chat-v3.1:free",  # 使用更常见的模型进行验证
                "messages": [
                    {
                        "role": "user",
                        "content": "test"  # 简化内容格式
                    }
                ],
                "max_tokens": 1  # 最小 token 数量，减少费用
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code == 401:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter API key 无效或已过期"
                )
            elif response.status_code == 402:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter 账户余额不足"
                )
            elif response.status_code == 429:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter API 调用频率过高"
                )
            elif response.status_code >= 500:
                raise ToolProviderCredentialValidationError(
                    "OpenRouter 服务器暂时不可用"
                )
            elif response.status_code not in [200, 400]:  # 400 可能是因为测试请求格式
                raise ToolProviderCredentialValidationError(
                    f"OpenRouter API 连接测试失败，状态码: {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            raise ToolProviderCredentialValidationError(
                "OpenRouter API 连接超时，请检查网络连接"
            )
        except requests.exceptions.ConnectionError:
            raise ToolProviderCredentialValidationError(
                "无法连接到 OpenRouter API，请检查网络连接"
            )
        except requests.exceptions.RequestException as e:
            raise ToolProviderCredentialValidationError(
                f"OpenRouter API 连接测试失败: {str(e)}"
            )