#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安推特监控机器人 - Twitter API v2版本
支持多token轮换，避免API限制
专门针对429错误进行优化的推特监控程序
"""

import logging
import time
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import requests
from dataclasses import dataclass

from twitter_api_manager import TwitterAPIManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tweet_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """配置类 - 支持多token"""
    
    def __init__(self):
        # Twitter API v2 多token配置 - 支持两种配置方式
        bearer_tokens_str = os.getenv('TWITTER_BEARER_TOKENS', '')
        if bearer_tokens_str:
            # 方式1：逗号分隔的多个token
            self.twitter_bearer_tokens = [token.strip() for token in bearer_tokens_str.split(',') if token.strip()]
        else:
            # 方式2：单独配置的多个token (TWITTER_BEARER_TOKEN_1, TWITTER_BEARER_TOKEN_2, ...)
            self.twitter_bearer_tokens = []
            
            # 检查单独的token配置
            for i in range(1, 21):  # 支持最多20个token
                token_key = f'TWITTER_BEARER_TOKEN_{i}' if i > 1 else 'TWITTER_BEARER_TOKEN'
                token = os.getenv(token_key, '')
                if token:
                    self.twitter_bearer_tokens.append(token)
            
            # 如果没有找到编号的token，检查基础token
            if not self.twitter_bearer_tokens:
                single_token = os.getenv('TWITTER_BEARER_TOKEN', '')
                if single_token:
                    self.twitter_bearer_tokens = [single_token]
        
        # 微信机器人配置
        self.wechat_webhook_url = os.getenv('WECHAT_WEBHOOK_URL', '')
        self.wechat_secret = os.getenv('WECHAT_SECRET', '')
        self.wechat_mentioned_list = os.getenv('WECHAT_MENTIONED_LIST', '').split(',') if os.getenv('WECHAT_MENTIONED_LIST') else []
        
        # 监控配置
        self.target_username = os.getenv('TARGET_USERNAME', 'binancezh')
        self.monitor_interval = int(os.getenv('MONITOR_INTERVAL', '1800'))
        
        # alpha积分关键词
        self.alpha_keywords = [
            'alpha', 'Alpha', 'ALPHA',
            '积分', 'points', 'Points', 'POINTS',
            '奖励', 'reward', 'Reward', 'REWARD',
            '空投', 'airdrop', 'Airdrop', 'AIRDROP',
            'aplha', 'Aplha', 'APLHA',  # 常见拼写错误
            'Alpha积分', 'alpha积分',
            '测试', 'test', 'Test'  # 可根据需要调整
        ]
        
        # 验证必要配置
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证必要的配置项"""
        if not self.twitter_bearer_tokens or not any(self.twitter_bearer_tokens):
            raise ValueError("缺少 TWITTER_BEARER_TOKENS 环境变量")
        if not self.wechat_webhook_url:
            logger.warning("缺少 WECHAT_WEBHOOK_URL，将无法发送微信通知")
        
        logger.info(f"配置了 {len(self.twitter_bearer_tokens)} 个Twitter API token")


class WeChatBot:
    """微信机器人"""
    
    def __init__(self, webhook_url: str, secret: str = '', mentioned_list: Optional[List[str]] = None):
        self.webhook_url = webhook_url
        self.secret = secret
        self.mentioned_list = mentioned_list or []
    
    def send_message(self, content: str) -> bool:
        """发送微信消息"""
        if not self.webhook_url:
            logger.warning("未配置微信webhook，跳过消息发送")
            return False
        
        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": content,
                    "mentioned_list": self.mentioned_list
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("微信消息发送成功")
                    return True
                else:
                    logger.error(f"微信消息发送失败: {result}")
            else:
                logger.error(f"微信API请求失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送微信消息异常: {e}")
        
        return False


class BinanceTweetMonitor:
    """币安推特监控器"""
    
    def __init__(self):
        self.config = Config()
        self.twitter_api = TwitterAPIManager(self.config.twitter_bearer_tokens)
        self.wechat_bot = WeChatBot(
            self.config.wechat_webhook_url,
            self.config.wechat_secret,
            self.config.wechat_mentioned_list
        )
        
        # 已处理推文记录
        self.processed_tweets_file = 'data/processed_tweets.json'
        self.processed_tweets = self._load_processed_tweets()
        
    def _load_processed_tweets(self) -> Dict[str, Any]:
        """加载已处理推文记录"""
        try:
            if os.path.exists(self.processed_tweets_file):
                with open(self.processed_tweets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载已处理推文记录失败: {e}")
        
        return {
            'tweets': [],
            'last_tweet_id': None,
            'last_update': None
        }
    
    def _save_processed_tweets(self) -> None:
        """保存已处理推文记录"""
        try:
            os.makedirs(os.path.dirname(self.processed_tweets_file), exist_ok=True)
            self.processed_tweets['last_update'] = datetime.now().isoformat()
            with open(self.processed_tweets_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_tweets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存已处理推文记录失败: {e}")
    
    def _is_monitoring_time(self) -> bool:
        """检查是否在监控时间范围内（北京时间11:00-23:00）"""
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = datetime.now(beijing_tz)
        current_hour = beijing_time.hour
        
        # 北京时间11点到23点
        return 11 <= current_hour <= 23
    
    def contains_alpha_keywords(self, text: str) -> bool:
        """检查文本是否包含alpha关键词"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.config.alpha_keywords)
    
    def format_message(self, tweet: Dict[str, Any]) -> str:
        """格式化推文消息"""
        beijing_tz = timezone(timedelta(hours=8))
        tweet_time = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
        beijing_time = tweet_time.astimezone(beijing_tz)
        
        return f"""🚀 币安Alpha积分推文提醒

📝 内容: {tweet['text']}

🕐 时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

🔗 链接: {tweet['url']}

💰 #币安 #Alpha积分 #推特监控"""
    
    def get_user_tweets(self) -> List[Dict[str, Any]]:
        """获取用户推文"""
        try:
            # 获取用户信息
            user = self.twitter_api.get_user_by_username(self.config.target_username)
            if not user:
                logger.error(f"用户 {self.config.target_username} 不存在或获取失败")
                return []
            
            # 获取推文
            since_id = self.processed_tweets.get('last_tweet_id')
            tweets = self.twitter_api.get_user_tweets(
                user['id'], 
                since_id=since_id, 
                max_results=10
            )
            
            if not tweets:
                logger.info("没有新推文")
                return []
            
            # 处理推文数据
            processed_tweets = []
            for tweet in tweets:
                tweet_data = {
                    'id': str(tweet['id']),
                    'text': tweet['text'],
                    'created_at': tweet['created_at'],
                    'url': f"https://twitter.com/{self.config.target_username}/status/{tweet['id']}"
                }
                processed_tweets.append(tweet_data)
            
            # 更新最后一条推文ID
            if processed_tweets:
                self.processed_tweets['last_tweet_id'] = processed_tweets[0]['id']
            
            logger.info(f"获取到 {len(processed_tweets)} 条新推文")
            return processed_tweets
            
        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return []
    
    def process_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理推文，筛选alpha相关内容"""
        alpha_tweets = []
        
        for tweet in tweets:
            # 跳过已处理的推文
            if tweet['id'] in self.processed_tweets['tweets']:
                continue
            
            # 检查是否包含alpha关键词
            if self.contains_alpha_keywords(tweet['text']):
                alpha_tweets.append(tweet)
                logger.info(f"发现alpha推文: {tweet['id']}")
            
            # 记录为已处理
            self.processed_tweets['tweets'].append(tweet['id'])
        
        # 只保留最近1000条记录，避免文件过大
        if len(self.processed_tweets['tweets']) > 1000:
            self.processed_tweets['tweets'] = self.processed_tweets['tweets'][-1000:]
        
        return alpha_tweets
    
    def send_notifications(self, tweets: List[Dict[str, Any]]) -> None:
        """发送通知"""
        for tweet in tweets:
            try:
                message = self.format_message(tweet)
                success = self.wechat_bot.send_message(message)
                if success:
                    logger.info(f"推文 {tweet['id']} 通知发送成功")
                else:
                    logger.error(f"推文 {tweet['id']} 通知发送失败")
                
                # 发送间隔
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"发送通知异常: {e}")
    
    def run(self) -> None:
        """运行监控"""
        try:
            logger.info("开始执行推特监控")
            
            # 检查是否在监控时间内
            if not self._is_monitoring_time():
                logger.info("当前不在监控时间范围内（北京时间11:00-23:00）")
                return
            
            # 输出token状态
            token_status = self.twitter_api.get_token_status()
            logger.info(f"Token状态: {json.dumps(token_status, indent=2, ensure_ascii=False)}")
            
            # 获取推文
            tweets = self.get_user_tweets()
            
            if tweets:
                # 处理推文
                alpha_tweets = self.process_tweets(tweets)
                
                if alpha_tweets:
                    # 发送通知
                    self.send_notifications(alpha_tweets)
                    logger.info(f"发现并处理了 {len(alpha_tweets)} 条alpha推文")
                else:
                    logger.info("未发现alpha相关推文")
            else:
                logger.info("没有新推文")
            
            # 保存处理记录
            self._save_processed_tweets()
            
            logger.info("监控执行完成")
            
        except Exception as e:
            logger.error(f"监控执行异常: {e}")
            sys.exit(1)


def main() -> None:
    """主函数"""
    try:
        # 创建必要目录
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # 运行监控
        monitor = BinanceTweetMonitor()
        monitor.run()
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()