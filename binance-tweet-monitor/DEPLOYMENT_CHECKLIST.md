# 🚀 部署检查清单

## ✅ 已完成的配置

根据你提供的GitHub Secrets截图，以下配置已完成：

### Twitter API Token配置 ✅
- `TWITTER_BEARER_TOKEN` - 主Token
- `TWITTER_BEARER_TOKEN_1` 到 `TWITTER_BEARER_TOKEN_8` - 额外的8个Token
- 总共9个Token，足够避免API限制问题

### 微信机器人配置 ✅
- `WECHAT_WEBHOOK_URL` - 企业微信机器人Webhook地址

## 📋 部署步骤

### 1. 上传代码到GitHub ✅
你只需要将项目文件推送到GitHub仓库即可。

### 2. 自动运行时间 📅
- **北京时间**: 每天中午11:00到晚上11:00
- **触发频率**: 每30分钟检查一次
- **UTC时间**: 03:00-15:00 (GitHub Actions使用UTC时间)

### 3. 监控内容 🔍
- 监控用户: `@binancezh`
- 关键词: alpha, Alpha, ALPHA, 积分, points, 奖励, reward, 空投, airdrop 等
- 拼写错误也会被捕获: aplha, Aplha, APLHA

## 🎯 推送代码后会发生什么

1. **立即触发**: 第一次推送会立即触发一次测试运行
2. **定时运行**: 之后按照设定的时间表自动运行
3. **Token轮换**: 系统会自动在9个Token之间轮换使用
4. **微信通知**: 发现相关推文时会自动发送到你的微信群

## 📊 监控运行状态

### 查看GitHub Actions
1. 进入你的GitHub项目
2. 点击 `Actions` 标签页
3. 查看 `Binance Tweet Monitor` 工作流
4. 点击具体的运行记录查看日志

### 日志信息包含
- Token使用状态
- API请求结果
- 发现的推文数量
- 微信通知发送状态
- 错误信息（如果有）

## 🔧 可选配置

### 如果需要修改监控时间
编辑 `.github/workflows/tweet-monitor.yml` 文件中的cron表达式：
```yaml
# 当前: 北京时间11:00-23:00，每30分钟
- cron: '0,30 3-15 * * *'

# 示例: 全天候每小时检查
# - cron: '0 * * * *'

# 示例: 只在工作日运行
# - cron: '0,30 3-15 * * 1-5'
```

### 如果需要修改关键词
编辑 `src/main.py` 文件中的 `alpha_keywords` 列表。

## ⚠️ 注意事项

1. **首次运行**: 推送代码后，GitHub Actions可能需要几分钟来启动
2. **Token安全**: 你的Token信息已安全存储在GitHub Secrets中
3. **API限制**: 9个Token足够处理高频监控，无需担心429错误
4. **时区设置**: 代码已设置为北京时间，消息中的时间显示正确

## 🚀 现在就可以部署！

你的配置已经完善，只需要：
1. 将代码推送到GitHub
2. 查看Actions运行状态
3. 等待推文通知

代码会自动处理所有的Token管理和错误恢复！