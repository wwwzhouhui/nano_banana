from dify_plugin import Plugin, DifyPluginEnv

# 配置插件环境
# OpenRouter API 通常响应较快，设置 60 秒超时
plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=60))

if __name__ == '__main__':
    plugin.run()