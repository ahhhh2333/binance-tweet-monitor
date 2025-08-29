#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试脚本
用于在部署到GitHub Actions前测试配置和功能
"""

import os
import sys
import logging
from typing import Dict, Any

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_env_from_file():
    """从.env文件加载环境变量（用于本地测试）"""
    env_file = '.env'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ 成功加载 .env 文件")
        except Exception as e:
            print(f"❌ 加载 .env 文件失败: {e}")
    else:
        print("⚠️  未找到 .env 文件，请确保已设置环境变量")

def check_config() -> Dict[str, Any]:
    """检查配置完整性"""
    results = {
        'twitter_config': False,
        'wechat_config': False,
        'missing_vars': [],
        'token_count': 0
    }
    
    # 检查Twitter配置 (支持多种格式)
    bearer_tokens_str = os.getenv('TWITTER_BEARER_TOKENS')
    bearer_token_single = os.getenv('TWITTER_BEARER_TOKEN')
    
    twitter_tokens = []
    
    if bearer_tokens_str:
        # 方式1：逗号分隔的多个token
        tokens = [token.strip() for token in bearer_tokens_str.split(',') if token.strip()]
        twitter_tokens.extend(tokens)
    else:
        # 方式2：单独配置的多个token
        for i in range(1, 21):  # 支持最多20个token
            token_key = f'TWITTER_BEARER_TOKEN_{i}' if i > 1 else 'TWITTER_BEARER_TOKEN'
            token = os.getenv(token_key)
            if token:
                twitter_tokens.append(token)
        
        # 如果没有编号token，检查基础token
        if not twitter_tokens and bearer_token_single:
            twitter_tokens.append(bearer_token_single)
    
    if twitter_tokens:
        results['twitter_config'] = True
        results['token_count'] = len(twitter_tokens)
        print(f"✅ Twitter API 配置完整，共 {len(twitter_tokens)} 个token")
        
        # 显示部分token信息（保护隐私）
        for i, token in enumerate(twitter_tokens[:3]):  # 只显示前3个
            masked = token[:10] + '...' + token[-4:] if len(token) > 14 else token
            print(f"  Token {i+1}: {masked}")
        if len(twitter_tokens) > 3:
            print(f"  ... 还有 {len(twitter_tokens) - 3} 个 token")
    else:
        print("❌ Twitter API 配置缺失: 需要 TWITTER_BEARER_TOKEN 或 TWITTER_BEARER_TOKEN_1 等")
        results['missing_vars'].append('TWITTER_BEARER_TOKEN')
    
    # 检查微信配置
    wechat_url = os.getenv('WECHAT_WEBHOOK_URL')
    if wechat_url:
        results['wechat_config'] = True
        print("✅ 微信机器人配置完整")
        # 显示部分URL（保护隐私）
        masked_url = wechat_url[:30] + '...' if len(wechat_url) > 30 else wechat_url
        print(f"  Webhook URL: {masked_url}")
    else:
        print("❌ 微信机器人配置缺失: WECHAT_WEBHOOK_URL")
        results['missing_vars'].append('WECHAT_WEBHOOK_URL')
    
    return results

def test_twitter_connection():
    """测试Twitter连接"""
    try:
        print("\n🔍 测试 Twitter API v2 连接...")
        
        # 导入主程序
        from main import BinanceTweetMonitor
        
        # 创建监控器实例
        monitor = BinanceTweetMonitor()
        
        # 显示token状态
        token_status = monitor.twitter_api.get_token_status()
        print(f"📊 Token状态:")
        for token_name, status in token_status.items():
            status_icon = "✅" if status['can_use'] else "❌"
            print(f"  {status_icon} {token_name}: {status['masked_token']} (使用次数: {status['usage_count']})")
        
        # 测试获取推文
        tweets = monitor.get_user_tweets()
        
        if tweets is not None:
            print(f"✅ Twitter API v2 连接成功，获取到 {len(tweets)} 条推文")
            
            # 显示最新推文示例
            if tweets:
                latest_tweet = tweets[0]
                print(f"📝 最新推文预览: {latest_tweet['text'][:100]}...")
                
                # 测试关键词检测
                has_alpha = monitor.contains_alpha_keywords(latest_tweet['text'])
                print(f"🔍 包含alpha关键词: {'是' if has_alpha else '否'}")
            
            return True
        else:
            print("❌ Twitter API v2 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Twitter API v2 测试失败: {e}")
        return False

def test_wechat_notification():
    """测试微信通知"""
    try:
        print("\n💬 测试微信通知...")
        
        from main import WeChatBot
        
        webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
        if not webhook_url:
            print("❌ 未配置微信webhook URL")
            return False
        
        # 创建微信机器人
        bot = WeChatBot(
            webhook_url=webhook_url,
            secret=os.getenv('WECHAT_SECRET', ''),
            mentioned_list=os.getenv('WECHAT_MENTIONED_LIST', '').split(',') if os.getenv('WECHAT_MENTIONED_LIST') else []
        )
        
        # 发送测试消息
        test_message = """🧪 币安推特监控测试消息

这是一条测试消息，确认微信机器人配置正确。

如果你收到了这条消息，说明配置成功！

#测试 #推特监控"""
        
        success = bot.send_message(test_message)
        
        if success:
            print("✅ 微信通知发送成功")
            return True
        else:
            print("❌ 微信通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 微信通知测试失败: {e}")
        return False

def create_env_template():
    """创建环境变量模板文件"""
    template = """# 币安推特监控配置模板
# 复制此文件为 .env 并填入你的实际配置

# Twitter API 配置 (必需)
TWITTER_BEARER_TOKEN=你的推特Bearer令牌
TWITTER_API_KEY=你的推特API密钥
TWITTER_API_SECRET=你的推特API密钥密码
TWITTER_ACCESS_TOKEN=你的推特访问令牌
TWITTER_ACCESS_TOKEN_SECRET=你的推特访问令牌密码

# 微信机器人配置 (必需)
WECHAT_WEBHOOK_URL=你的企业微信机器人webhook地址
WECHAT_SECRET=你的企业微信机器人密钥(可选)
WECHAT_MENTIONED_LIST=@的用户列表,用逗号分隔(可选)

# 监控配置 (可选)
TARGET_USERNAME=binancezh
MONITOR_INTERVAL=300
"""
    
    try:
        with open('.env.template', 'w', encoding='utf-8') as f:
            f.write(template)
        print("✅ 已创建 .env.template 配置模板文件")
    except Exception as e:
        print(f"❌ 创建配置模板失败: {e}")

def main():
    """主测试函数"""
    print("🚀 币安推特监控 v2.0 - 本地测试")
    print("=" * 50)
    
    # 创建必要目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 加载环境变量
    load_env_from_file()
    
    # 检查配置
    print("\n📋 检查配置...")
    config_results = check_config()
    
    if config_results['missing_vars']:
        print(f"\n❌ 配置不完整，缺少以下环境变量:")
        for var in config_results['missing_vars']:
            print(f"   - {var}")
        
        print("\n💡 请按以下步骤配置:")
        print("1. 创建 .env 文件")
        print("2. 参考 .env.template 填入你的配置")
        print("3. 对于Twitter API，建议配置多个Bearer Token以获得更好的效果")
        print("4. 重新运行测试")
        
        create_env_template()
        return
    
    # 测试功能
    all_tests_passed = True
    
    # 测试Twitter连接
    if config_results['twitter_config']:
        twitter_ok = test_twitter_connection()
        all_tests_passed = all_tests_passed and twitter_ok
    
    # 测试微信通知
    if config_results['wechat_config']:
        wechat_ok = test_wechat_notification()
        all_tests_passed = all_tests_passed and wechat_ok
    
    # 总结
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 所有测试通过！你可以部署到GitHub Actions了")
        print(f"\n📊 配置概要:")
        print(f"  - Twitter Token数量: {config_results['token_count']}")
        print(f"  - 微信通知: {'已配置' if config_results['wechat_config'] else '未配置'}")
        print("\n📝 下一步:")
        print("1. 将配置添加到GitHub Secrets")
        print("2. 推送代码到GitHub")
        print("3. 查看Actions运行状态")
    else:
        print("❌ 部分测试失败，请检查配置后重试")

if __name__ == "__main__":
    main()