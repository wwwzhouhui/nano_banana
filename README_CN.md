中文 ｜ [English](./README.md)

[项目源码地址](https://github.com/wwwzhouhui/nano_banana)：

# 🍌 Nano Banana OpenRouter 文生图插件

> 基于 OpenRouter API 的高质量 AI 文生图 Dify 插件，支持多种先进的图像生成模型

## ✨ 特性

- 🎨 **多模型支持**: 支持 Google Gemini、OpenAI DALL-E、Anthropic Claude 等多种图像生成模型
- 🆓 **免费选项**: 提供免费的 Gemini 模型选项，适合测试和轻量使用
- 💎 **高质量输出**: 支持付费高端模型，提供专业级图像质量
- 🔄 **图像转换**: 支持图像到图像的转换功能
- 🌐 **多语言**: 完整的中英文双语支持
- ⚡ **实时反馈**: 详细的生成进度和状态反馈
- 🛡️ **错误处理**: 完善的错误处理和用户友好的提示

## 🚀 快速开始

### 1. 获取 OpenRouter API Key

1. 访问 [OpenRouter](https://openrouter.ai/keys)
2. 创建账户并生成 API Key
3. 复制您的 API Key (格式: `sk-or-v1-xxxxxx`)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加您的 API Key
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### 4. 测试插件

```bash
# 测试 API 连接
python tests/test_openrouter_api.py

# 测试完整插件功能
python tests/test_plugin.py
```

## 🎯 支持的模型

### 免费模型
- **Google Gemini 2.5 Flash**: 快速且质量良好，适合日常使用

### 付费模型
- **OpenAI DALL-E 3**: 最高质量的图像生成
- **Anthropic Claude 3.5 Sonnet**: 创意和艺术风格图像

## 📖 使用示例

###   离线安装插件

  ![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601091330.png)

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601136039.png)



 安装完成后，点击右边授权，填写openrouter apikey

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601191776.png)

### Agent 使用

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601261838.png)



![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601417171.png)

### chatflow使用

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756601616026.png)

 提示词

```
I'll transform the photo into a character figure scene. The character will stand on a round plastic base, with a box featuring its image behind and a computer displaying Blender modeling. The PVC material will look clear, and the setting will be indoors.
```

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756602734218.png)

![img](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/QQ_1756603375326.png)



## 🛠️ 开发指南

### 项目结构

```
nano-banana/
├── manifest.yaml              # 插件配置
├── main.py                   # 插件入口
├── requirements.txt          # 依赖管理
├── provider/                 # OpenRouter 服务提供者
│   ├── openrouter.yaml
│   └── openrouter_provider.py
├── tools/                    # 文生图工具
│   ├── text2image.yaml
│   └── text2image.py
└── tests/                    # 测试文件
    ├── test_openrouter_api.py
    └── test_plugin.py
```

### 核心组件

1. **OpenRouterProvider**: 管理 API 认证和连接验证
2. **Text2ImageTool**: 实现文生图核心逻辑
3. **错误处理**: 完善的异常处理和用户提示

## 🔧 配置说明

### API Key 配置
- 在 Dify 插件配置中输入您的 OpenRouter API Key
- 确保 API Key 格式正确 (`sk-or-v1-xxxxxx`)
- 确认账户有足够余额（付费模型需要）

### 模型选择建议
- **测试阶段**: 使用免费的 Gemini 模型
- **生产环境**: 根据质量需求选择付费模型
- **艺术创作**: 推荐 Claude 3.5 Sonnet
- **通用高质量**: 推荐 DALL-E 3

## 📊 性能优化

- **超时设置**: 60 秒请求超时，适合图像生成任务
- **错误重试**: 智能错误处理和重试建议
- **内存管理**: 高效的图像数据处理
- **格式统一**: 统一输出 PNG 格式确保兼容性

## 🐛 故障排除

### 常见问题

1. **API Key 无效**
   - 检查 API Key 格式是否正确
   - 确认 API Key 未过期
   - 验证账户状态

2. **余额不足**
   - 前往 [OpenRouter Credits](https://openrouter.ai/credits) 充值
   - 使用免费模型进行测试

3. **生成失败**
   - 检查提示词是否包含敏感内容
   - 尝试更换模型
   - 简化提示词描述

4. **网络问题**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试稍后重试

## 📝 更新日志

### v0.0.1 (2025-08-30)
- ✨ 初始版本发布
- 🔧 基于 OpenRouter API 的完整实现
- 🎨 支持多种图像生成模型
- 🧪 完整的测试框架
- 📖 详细的文档和使用指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [OpenRouter API 文档](https://openrouter.ai/docs)
- [Dify 插件开发文档](https://docs.dify.ai/plugins)
- [项目开发规范](../CLAUDE3_OpenRouter.md)

---

**Nano Banana** - 让 AI 图像生成变得简单而强大！ 🍌✨