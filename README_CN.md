中文 ｜ [English](./README.md)

[项目源码地址](https://github.com/wwwzhouhui/nano_banana)：

# 🍌 Nano Banana OpenRouter 文生图插件

> 基于 OpenRouter API 的高质量 AI 文生图 Dify 插件，支持多种先进的图像生成模型

## ✨ 特性

- 🎨 **多模型支持**: 支持 OpenRouter 上的 Gemini 图像预览模型等图像生成模型
- 📝 **纯文生图可用**: 只传提示词即可生成图片，不强制要求传入图片
- 🔄 **图生图支持**: 支持通过 Dify 文件输入或真实公网图片 URL 做图像转换
- 🔗 **Dify 内部图片直读**: 支持直接读取 Dify File 对象的二进制内容（`.blob`），自动转 base64 发送给 OpenRouter，无需公网 URL
- 🏠 **本地部署友好**: 自动识别 Dify 内部文件路径（`/files/...`），通过 Docker 内网下载图片并转 base64，无需公网 IP
- 🧠 **更安全的输入处理**: 当工作流传入 `1756601479774.picture.url` 这类占位变量时，会自动忽略并按未传图片处理
- 🖼️ **更稳健的结果解析**: 同时兼容 OpenRouter 的 `message.images[*].image_url.url` 和分段 `message.content[*].image_url.url` 返回结构
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

### 内置模型
- **Google Gemini 3.1 Flash Image Preview** (`google/gemini-3.1-flash-image-preview`)：默认快速模型，适合大多数文生图和图生图场景
- **Google Gemini 3 Pro Image Preview** (`google/gemini-3-pro-image-preview`)：更高质量选项，适合对画质要求更高的场景

### 手工模型覆盖
- 你也可以通过 `model_manual` 手工填写任意兼容的 OpenRouter 模型 ID
- 当填写了 `model_manual` 时，会覆盖下拉框中的模型选择

## 📖 使用示例

### 输入模式

#### 1. 纯文生图
不传 `input_image` 和 `input_image_url`，插件会仅使用提示词请求 OpenRouter。

#### 2. 使用 Dify 文件输入做图生图（推荐）
在工作流中把图片文件变量绑定到 `input_image`。这是 Dify 场景下推荐的方式。

#### 3. 使用公网 URL 兜底做图生图
如果你已经有真实可访问的公网图片地址，可以传给 `input_image_url`。

### 可选图片输入说明

- `input_image` 的优先级高于 `input_image_url`
- 当 `input_image` 是 Dify File 对象时，插件会优先通过 `.blob` 直接读取二进制内容，转 base64 后发送给 OpenRouter
- 如果 `.blob` 不可用，会从 File 对象的 URL 字段下载图片
- `input_image_url` 支持公网 `http(s)` URL、`data:image/...` URL，以及 Dify 内部文件路径（`/files/...`，需配置 `INTERNAL_FILES_URL`）
- 如果工作流绑定后传来类似 `1756601479774.picture.url` 这样的占位值，而实际没有上传图片，插件会按”未传图片”处理，继续走纯文生图
- OpenRouter 返回图片时，插件会同时解析 `message.images` 和分段 `message.content` 两种结构

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
- 确认所选模型对应的账户余额充足

### 图片输入配置
- 在 Dify 工作流上传图片或引用上游图片结果时，优先使用 `input_image`
- 只有在你明确拥有真实公网图片地址或 `data:image/...` 时，才使用 `input_image_url`
- 不建议手动把工作流占位字符串当成图片 URL 传入

### 模型选择建议
- **默认 / 快速迭代**: 使用 `Google Gemini 3.1 Flash Image Preview`
- **更高质量输出**: 使用 `Google Gemini 3 Pro Image Preview`
- **自定义 OpenRouter 模型**: 如果下拉列表中没有你需要的模型，可以填写 `model_manual`

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
   - 如果是图生图场景，优先使用 `input_image` 而不是 `input_image_url`

4. **图片输入未生效**
   - 确认工作流中上传的图片绑定到了 `input_image`
   - 如果 `input_image_url` 里是占位值而不是真实 URL，插件会自动忽略并继续纯文生图
   - 如果确实要通过 URL 传图，请提供真实可访问的公网 `http(s)` URL 或 `data:image/...`

5. **网络问题**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试稍后重试

6. **本地部署图生图 Connection refused**
   - 在 Dify 的 `.env` 中设置 `INTERNAL_FILES_URL=http://api:5001`
   - 确保 `FILES_URL` 也已配置（如 `FILES_URL=http://api:5001` 或 `FILES_URL=http://你的主机IP:5001`）
   - 修改后执行 `docker compose down && docker compose up -d` 重启 Dify
   - 插件会优先通过 Docker 内网地址下载图片，转成 base64 后发送给 OpenRouter

## 📝 更新日志

### v0.0.5 (2026-03-08)
- 🔗 新增 Dify File 对象 `.blob` 直读支持，上传图片自动转 base64 发给 OpenRouter，无需公网 URL
- 🏠 新增 Dify 内部文件路径（`/files/...`）自动解析，优先使用 `INTERNAL_FILES_URL` / `DIFY_INNER_API_URL` 等 Docker 内网地址
- 🐛 修复本地部署（无公网 IP）场景下图生图功能 Connection refused 报错
- 🧠 增强 `_iter_image_reference_candidates`，支持从 Dify File 对象属性中提取 URL 作为兜底
- ⚠️ Dify 内部路径无法解析时，给出明确的 `FILES_URL` 配置指引

### v0.0.4 (2026-03-07)
- 🔖 插件版本更新到 0.0.4
- 📝 同步文档中的最新版本信息
- 🖼️ 优化 Dify 工作流中的可选图片输入处理
- 🧠 当未实际上传图片时，自动忽略占位型 `input_image_url`，保证纯文生图继续可用
- 🔍 同时支持从 `message.images` 和分段 `message.content` 中提取 OpenRouter 返回图片

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