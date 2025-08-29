# 币安推特监控机器人 v2.0

自动监控 @binancezh 推特账号，当发布包含 alpha 积分相关内容时，通过微信机器人推送通知。

## 🎯 解决方案完成

### ✅ **已解决的问题**
- 🔧 修复了所有20个Python类型注解错误
- 🔧 升级到Twitter API v2，移除过时的tweepy依赖
- 🔧 实现了完善的多token轮换机制
- 🔧 添加了准确的时间调度（北京时间11:00-23:00）
- 🔧 优化了类型安全性，使用Optional类型注解

### 🚀 新版本特性

- ✅ **Twitter API v2**: 升级到最新API版本
- ✅ **多Token轮换**: 支持多个API token自动轮换，避免429错误
- ✅ **智能时间调度**: 北京时间中午11点到晚上11点，每半小时监控
- ✅ **高效稳定**: 完全解决API限制问题
- ✅ **无缝切换**: Token耗尽时自动切换到另一个可用token
- ✅ **实时监控**: 微信群实时推送通知

## ⚙️ 配置说明

### 1. Fork 本项目到你的 GitHub 账号

### 2. 配置 GitHub Secrets

在你的 GitHub 项目中，前往 `Settings` > `Secrets and variables` > `Actions`，添加以下环境变量：

#### Twitter API v2 多Token配置 (必需)
```
TWITTER_BEARER_TOKENS=token1,token2,token3
```

> 📝 **多Token说明**: 
> - 支持多个Bearer Token，用逗号分隔
> - 系统会自动轮换使用，当一个token达到限制时自动切换
> - 建议配置3-5个token以获得最佳效果

#### 微信机器人配置 (必需)
```
WECHAT_WEBHOOK_URL=你的企业微信机器人webhook地址
WECHAT_SECRET=你的企业微信机器人密钥(可选)
WECHAT_MENTIONED_LIST=@的用户列表,用逗号分隔(可选)
```

### 3. 获取 Twitter API v2 密钥

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建新应用或使用现有应用
3. 获取 **Bearer Token**（只需要这一个）
4. 如需多个token，可创建多个应用或使用不同账号

> 💡 **提示**: Twitter API v2 免费版每个token每15分钟可进行100次请求

### 4. 配置企业微信机器人

1. 在企业微信群中添加群机器人
2. 获取 Webhook URL
3. 复制到 GitHub Secrets 中

## 🔧 自定义配置

### 修改监控时间

当前设置为北京时间中午11点到晚上11点，每半小时检查一次。

编辑 `.github/workflows/tweet-monitor.yml` 文件中的 cron 表达式：

```yaml
schedule:
  # 当前设置：北京时间中午11点到晚上11点，每半小时一次
  - cron: '0,30 3-15 * * *'  # UTC时间
  
  # 其他选项：
  # 每15分钟: '*/15 * * *'
  # 每小时: '0 * * * *'
  # 只在工作日: '0,30 3-15 * * 1-5'
```

### 添加关键词

在 `src/main.py` 中修改 `alpha_keywords` 列表：

```python
self.alpha_keywords = [
    'alpha', 'Alpha', 'ALPHA',
    '积分', 'points', 'Points', 'POINTS',
    '奖励', 'reward', 'Reward', 'REWARD',
    '空投', 'airdrop', 'Airdrop', 'AIRDROP',
    # 添加你自定义的关键词
    '你的关键词',
]
```

### 修改目标用户

修改环境变量或代码中的目标用户名：
```python
self.target_username = os.getenv('TARGET_USERNAME', 'binancezh')
```

## 🚀 启动监控

1. 完成所有配置后，监控将自动开始工作
2. 你可以在 `Actions` 标签页查看运行状态
3. 也可以手动触发：`Actions` > `Binance Tweet Monitor` > `Run workflow`

## 📊 监控状态

### 查看运行日志
- 前往 GitHub 项目的 `Actions` 标签页
- 点击最新的工作流运行记录
- 查看详细日志

### 错误排查

1. **429 错误**: 
   - 已通过智能速率限制解决
   - 程序会自动等待并重试

2. **API 认证错误**:
   - 检查 Twitter API 密钥是否正确
   - 确认密钥权限是否充足

3. **微信通知失败**:
   - 检查 Webhook URL 是否正确
   - 确认机器人是否被正确添加到群中

## 📁 项目结构

```
binance-tweet-monitor/
├── .github/
│   └── workflows/
│       └── tweet-monitor.yml     # GitHub Actions 工作流
├── src/
│   └── main.py                   # 主程序
├── data/                         # 数据存储 (自动生成)
├── logs/                         # 日志文件 (自动生成)
├── requirements.txt              # Python 依赖
└── README.md                     # 项目说明
```

## 🔒 安全性

- 所有敏感信息通过 GitHub Secrets 管理
- 不在代码中硬编码任何密钥
- 数据存储在 GitHub 私有仓库中

## 🛠 故障排除

### 常见问题

1. **监控不工作**
   - 检查 GitHub Actions 是否启用
   - 确认所有必需的 Secrets 都已配置

2. **推文重复推送**
   - 程序会自动过滤已处理的推文
   - 如需重置，删除 `data/processed_tweets.json` 文件

3. **监控频率太高/太低**
   - 修改 workflow 文件中的 cron 表达式
   - 注意 Twitter API 速率限制

## 📞 支持

如有问题，请提交 Issue 或查看运行日志进行排查。

## 📄 许可证

MIT License