# 币安推特监控机器人

一个自动监控 @binancezh 推特账号 Alpha 积分相关推文并推送到企业微信的机器人。支持多 Token 轮换，避免 API 限制，完全基于 GitHub Actions 云端运行。

## ✨ 功能特点

- 🚀 **自动监控**：实时监控 @binancezh 推特账号的最新推文
- 🔍 **智能识别**：自动识别包含 "Alpha积分" 相关关键词的推文
- 📱 **微信推送**：自动推送到企业微信群，支持完整推文内容显示
- 🔄 **多Token轮换**：支持最多8个Twitter API Token轮换使用，避免429错误
- ⏰ **定时执行**：北京时间11:00-23:00每30分钟自动检查一次
- 🚫 **去重机制**：避免重复推送相同推文
- ☁️ **云端运行**：基于GitHub Actions，无需本地部署

## 📋 项目结构
binance-tweet-monitor/
├── main.py # 主程序脚本
├── test_local.py # 本地测试脚本
├── requirements.txt # Python依赖
├── .github/workflows/
│ └── tweet-monitor.yml # GitHub Actions配置
├── processed_tweets.json # 已处理推文记录（自动生成）
└── README.md # 项目说明

## 🚀 快速开始

### 1. 准备工作

#### 获取 Twitter API Token
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建开发者账号并申请 API 访问权限
3. 创建一个新的 App
4. 获取 Bearer Token（建议申请3-8个不同的开发者账号以获得更多Token）

#### 获取企业微信机器人 Webhook
1. 在企业微信群中添加机器人
2. 获取 Webhook URL（格式类似：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx`）

### 2. 部署到 GitHub

#### Step 1: Fork 或下载本项目
```bash
git clone https://github.com/yourusername/binance-tweet-monitor.git
cd binance-tweet-monitor
Step 2: 配置 GitHub Secrets
在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下配置：

Twitter API Tokens（至少配置1个，建议3-8个）：

TWITTER_BEARER_TOKEN_1
TWITTER_BEARER_TOKEN_2
TWITTER_BEARER_TOKEN_3
TWITTER_BEARER_TOKEN_4
TWITTER_BEARER_TOKEN_5
TWITTER_BEARER_TOKEN_6
TWITTER_BEARER_TOKEN_7
TWITTER_BEARER_TOKEN_8
企业微信配置：

WECHAT_WEBHOOK_URL
Step 3: 推送代码，自动运行
git add .
git commit -m "Initial setup"
git push origin main

推送后，GitHub Actions 会自动开始运行，按照设定的时间表进行监控。

3. 本地测试（可选）
如果想在本地测试配置：
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
export TWITTER_BEARER_TOKEN_1="your_token_here"
export WECHAT_WEBHOOK_URL="your_webhook_url_here"

# 3. 运行测试
python test_local.py

# 4. 运行主程序
python main.py
⚙️ 配置说明
Twitter API Token 获取建议
为了最大化可用性，建议：

申请3-5个不同的 Twitter 开发者账号
每个账号创建独立的 App 获取 Bearer Token
避免在同一账号下创建多个 App（可能共享限制）
监控关键词
当前监控的关键词包括：

alpha, Alpha, ALPHA
积分, points, Points, point, Point
Alpha积分, alpha积分, Alpha Points, alpha points
可以在 main.py 中的 alpha_keywords 列表中修改。
间调度
运行时间：北京时间 11:00-23:00
检查频率：每30分钟一次
非运行时间：程序会自动跳过执行
📱 推送示例
当检测到 Alpha 积分相关推文时，会收到如下格式的企业微信消息：
🚀 币安Alpha积分推文提醒

📝 内容: 币安 Alpha 宣告个上线 CeluvPlay (CELB) 的平台，Alpha 交易
客户 2025 年 8 月 29 日 17:00 (UTC+8) 开始。

⚡ 交易开始后，持有至少 220 个币安 Alpha 积分的用户可获得 3,200 个
CELB 代币奖励。先到先得，若活动未结束，则为期1年结活动低
15 分。

请注意，申领空投将消耗 15 个币安

🕐 时间: 2025-08-29 15:30:16 (北京时间)

🔗 链接: https://twitter.com/binancezh/status/1961330456879862178

💰 #币安 #Alpha积分 #推特监控

🔧 高级配置
自定义监控时间
修改 .github/workflows/tweet-monitor.yml 中的 cron 表达式：
schedule:
  # 当前：北京时间11:00-23:00，每30分钟
  - cron: '0,30 3-15 * * *'
  
  # 示例：北京时间9:00-21:00，每小时
  # - cron: '0 1-13 * * *'
添加更多关键词
在 main.py 中修改 alpha_keywords 列表：
self.alpha_keywords = [
    'alpha', 'Alpha', 'ALPHA',
    '积分', 'points', 'Points',
    # 添加更多关键词
    '新币', 'listing', 'airdrop'
]
