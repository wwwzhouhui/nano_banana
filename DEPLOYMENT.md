# 🚀 Nano Banana OpenRouter 文生图插件部署指南

## 📋 部署前准备

### 1. 环境要求
- Python 3.12+
- Dify 平台环境
- 稳定的网络连接

### 2. API Key 准备
- OpenRouter 账户和有效的 API Key
- 确保账户有足够余额（使用付费模型时）

## 🔧 本地开发部署

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd nano-banana
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，添加您的 OpenRouter API Key
```

### 4. 运行测试
```bash
# 测试 API 连接
python tests/test_openrouter_api.py

# 测试插件功能
python tests/test_plugin.py
```

## 🌐 Dify 平台部署

### 1. 插件打包
确保所有文件完整：
```
nano-banana/
├── manifest.yaml
├── main.py
├── requirements.txt
├── provider/
├── tools/
└── _assets/
```

### 2. 上传到 Dify
1. 将整个 `nano-banana` 文件夹打包为 ZIP 文件
2. 在 Dify 管理界面上传插件包
3. 等待插件安装完成

### 3. 配置 API Key
1. 在 Dify 插件管理中找到 "Nano Banana Text2Image"
2. 点击配置，输入您的 OpenRouter API Key
3. 保存配置

### 4. 测试部署
1. 创建新的工作流
2. 添加 "Nano Banana Text2Image" 工具
3. 输入测试提示词进行验证

## ⚙️ 生产环境配置

### 1. 性能优化
```yaml
# manifest.yaml 中的资源配置
resource:
  memory: 2097152  # 2GB 内存（可根据需要调整）
  permission:
    model:
      enabled: true
      llm: true
    tool:
      enabled: true
```

### 2. 安全配置
- 使用生产环境专用的 API Key
- 设置适当的访问权限
- 定期轮换 API Key

### 3. 监控配置
- 监控 API 调用频率
- 跟踪 Token 使用量
- 设置余额告警

## 🔍 部署验证

### 1. 功能测试清单
- [ ] 插件成功安装
- [ ] API Key 配置正确
- [ ] 基础文生图功能正常
- [ ] 多模型切换正常
- [ ] 错误处理正确
- [ ] 图像输出格式正确

### 2. 性能测试
- [ ] 响应时间在可接受范围内
- [ ] 内存使用正常
- [ ] 并发请求处理正常

### 3. 安全测试
- [ ] API Key 安全存储
- [ ] 敏感信息不泄露
- [ ] 输入验证正确

## 🐛 常见部署问题

### 1. 插件安装失败
**问题**: 插件包上传失败
**解决方案**:
- 检查文件结构是否正确
- 确认 manifest.yaml 格式正确
- 检查文件权限

### 2. API Key 验证失败
**问题**: 提示 API Key 无效
**解决方案**:
- 确认 API Key 格式正确 (`sk-or-v1-xxxxxx`)
- 检查 API Key 是否过期
- 验证网络连接

### 3. 图像生成失败
**问题**: 工具调用失败
**解决方案**:
- 检查账户余额
- 验证模型可用性
- 检查提示词内容

### 4. 性能问题
**问题**: 响应时间过长
**解决方案**:
- 增加内存配置
- 优化网络连接
- 选择更快的模型

## 📊 监控和维护

### 1. 日志监控
- 监控插件运行日志
- 跟踪错误频率
- 分析性能指标

### 2. 使用统计
- Token 消耗统计
- 模型使用分布
- 用户使用模式

### 3. 定期维护
- 更新依赖包
- 检查 API 兼容性
- 优化配置参数

## 🔄 版本升级

### 1. 升级准备
- 备份当前配置
- 测试新版本兼容性
- 准备回滚方案

### 2. 升级步骤
1. 下载新版本插件包
2. 在测试环境验证
3. 备份生产环境
4. 执行升级
5. 验证功能正常

### 3. 回滚方案
- 保留旧版本备份
- 快速回滚流程
- 数据恢复方案

## 📞 技术支持

### 遇到问题？
1. 查看本部署指南
2. 检查 [README.md](README.md) 中的故障排除
3. 查看项目 Issues
4. 联系技术支持

### 反馈渠道
- GitHub Issues
- 技术支持邮箱
- 社区论坛

---

**祝您部署顺利！** 🍌✨

如有任何问题，请随时联系我们的技术支持团队。