# 🚀 GitHub Actions 部署指南

## 📋 准备工作

### 1. 获取 Twitter API 密钥

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 登录并创建新的应用
3. 申请 API 访问权限（免费版即可）
4. 获取以下密钥：
   - `Bearer Token`
   - `API Key` 和 `API Secret`
   - `Access Token` 和 `Access Token Secret`

> 💡 **注意**: 免费版 Twitter API 每15分钟允许75次请求，足够监控使用

### 2. 配置企业微信机器人

1. 在企业微信群中添加群机器人
2. 获取 Webhook URL（格式类似：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx`）
3. 可选：配置机器人安全设置

## 🔧 部署步骤

### 步骤 1: Fork 项目

1. 访问你的项目：https://github.com/ahhhh2333/binance-tweet-monitor
2. 点击右上角的 `Fork` 按钮
3. Fork 到你的 GitHub 账号

### 步骤 2: 配置 GitHub Secrets

1. 进入你 Fork 的项目
2. 点击 `Settings` 标签页
3. 在左侧菜单选择 `Secrets and variables` > `Actions`
4. 点击 `New repository secret` 添加以下配置：

#### 必需配置
```
名称: TWITTER_BEARER_TOKEN
值: 你的推特Bearer令牌

名称: TWITTER_API_KEY
值: 你的推特API密钥

名称: TWITTER_API_SECRET
值: 你的推特API密钥密码

名称: TWITTER_ACCESS_TOKEN
值: 你的推特访问令牌

名称: TWITTER_ACCESS_TOKEN_SECRET
值: 你的推特访问令牌密码

名称: WECHAT_WEBHOOK_URL
值: 你的企业微信机器人webhook地址
```

#### 可选配置
```
名称: WECHAT_SECRET
值: 你的企业微信机器人密钥

名称: WECHAT_MENTIONED_LIST
值: @的用户列表,用逗号分隔

名称: TARGET_USERNAME
值: binancezh (默认值，可不设置)

名称: MONITOR_INTERVAL
值: 300 (默认值，可不设置)
```

### 步骤 3: 启动 Actions

1. 推送代码到 main 分支（自动触发）
2. 或者手动触发：
   - 点击 `Actions` 标签页
   - 选择 `Binance Tweet Monitor` 工作流
   - 点击 `Run workflow` 按钮

### 步骤 4: 验证运行

1. 在 `Actions` 页面查看工作流运行状态
2. 点击具体的运行记录查看详细日志
3. 确认没有错误信息

## 📊 监控配置

### 调整监控频率

编辑 `.github/workflows/tweet-monitor.yml` 文件中的 cron 表达式：

```yaml
schedule:
  # 当前设置：每5分钟检查一次
  - cron: '*/5 * * * *'
  
  # 其他选项：
  # 每10分钟: '*/10 * * * *'
  # 每30分钟: '*/30 * * * *'
  # 每小时: '0 * * * *'
  # 每2小时: '0 */2 * * *'
```

> ⚠️ **重要**: 过于频繁的检查可能触发 Twitter API 速率限制

### 修改关键词

在 `src/main.py` 中修改 `alpha_keywords` 列表：

```python
self.alpha_keywords = [
    'alpha', 'Alpha', 'ALPHA',
    '积分', 'points', 'Points', 'POINTS',
    '奖励', 'reward', 'Reward', 'REWARD',
    '空投', 'airdrop', 'Airdrop', 'AIRDROP',
    # 添加你的自定义关键词
    '新关键词1',
    '新关键词2',
]
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. 429 错误 (Too Many Requests)
**原因**: API请求过于频繁
**解决方案**: 
- 程序已内置智能速率限制
- 如仍出现，调低监控频率
- 检查是否有其他程序使用相同的 Twitter API

#### 2. 401 错误 (Unauthorized)
**原因**: API 认证失败
**解决方案**:
- 检查所有 Twitter API 密钥是否正确
- 确认 API 密钥权限是否充足
- 重新生成 API 密钥

#### 3. 微信消息发送失败
**原因**: 微信机器人配置问题
**解决方案**:
- 检查 Webhook URL 是否正确
- 确认机器人是否被正确添加到群中
- 测试 Webhook URL 是否可访问

#### 4. 工作流不运行
**原因**: GitHub Actions 设置问题
**解决方案**:
- 确认 Actions 已启用
- 检查 cron 表达式格式
- 手动触发测试

### 查看详细日志

1. 前往 `Actions` 标签页
2. 点击对应的工作流运行
3. 展开各个步骤查看详细输出
4. 查找错误信息和警告

## 🎛️ 高级配置

### 多账号监控

如需监控多个 Twitter 账号，可以：

1. 复制工作流文件，修改不同的目标用户名
2. 或在代码中添加多账号支持逻辑

### 自定义通知格式

修改 `src/main.py` 中的 `format_message` 方法：

```python
def format_message(self, tweet: Dict) -> str:
    """自定义消息格式"""
    return f"""🚀 自定义通知格式

📝 内容: {tweet['text']}
🕐 时间: {tweet['created_at']}
🔗 链接: {tweet['url']}

#自定义标签"""
```

### 添加其他通知方式

可以在代码中添加：
- 钉钉机器人通知
- Slack 通知
- 邮件通知
- Telegram 通知

## 📈 性能优化

### 数据存储优化

项目会自动管理数据文件：
- `data/processed_tweets.json`: 存储已处理推文ID
- `data/rate_limit_history.json`: 存储API请求历史
- `logs/`: 存储运行日志

这些文件会自动清理，避免占用过多空间。

### 成本控制

GitHub Actions 免费额度：
- 公共仓库：无限制
- 私有仓库：每月2000分钟

当前配置每次运行约1-2分钟，完全在免费额度内。

## 🔒 安全建议

1. **使用私有仓库**: 避免泄露配置信息
2. **定期更新密钥**: 建议每3-6个月更新一次API密钥
3. **最小权限原则**: 只给予必要的API权限
4. **监控访问**: 定期检查API使用情况

## 📞 获取帮助

如果遇到问题：

1. 查看 [常见问题](#故障排除)
2. 检查运行日志
3. 提交 GitHub Issue
4. 参考 Twitter API 官方文档

## 🎯 总结

完成以上步骤后，你的推特监控系统将：

- ✅ 每5分钟自动检查 @binancezh 的新推文
- ✅ 智能识别包含 alpha 积分的内容
- ✅ 自动发送微信通知
- ✅ 避免重复推送
- ✅ 完美处理 API 速率限制

享受全自动的推特监控体验！🚀