#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安推特监控机器人 - 简化版
监控@binancezh的Alpha积分推文并自动推送到企业微信
"""

import os
import json
import time
import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BinanceTwitterMonitor:
    def __init__(self):
        # 获取配置
        self.bearer_tokens = self._get_bearer_tokens()
        self.wechat_webhook = os.getenv('WECHAT_WEBHOOK_URL', '')
        self.target_user = 'binancezh'
        self.current_token_index = 0
        
        # Alpha关键词
        self.alpha_keywords = [
            'alpha', 'Alpha', 'ALPHA', 'aplha', 'Aplha',
            '积分', 'points', 'Points', 'point', 'Point',
            'Alpha积分', 'alpha积分', 'Alpha Points', 'alpha points'
        ]
        
        # 数据文件
        self.data_file = 'processed_tweets.json'
        self.processed_ids = self._load_processed_tweets()
        
        logger.info(f"初始化完成，共{len(self.bearer_tokens)}个Token")
    
    def _get_bearer_tokens(self) -> List[str]:
        """获取所有Bearer Token"""
        tokens = []
        
        # 获取编号的token (1-8)
        for i in range(1, 9):
            token = os.getenv(f'TWITTER_BEARER_TOKEN_{i}', '')
            if token:
                tokens.append(token)
        
        # 如果没有编号token，尝试获取基础token
        if not tokens:
            base_token = os.getenv('TWITTER_BEARER_TOKEN', '')
            if base_token:
                tokens.append(base_token)
        
        if not tokens:
            raise ValueError("未找到Twitter Bearer Token")
        
        return tokens
    
    def _load_processed_tweets(self) -> List[str]:
        """加载已处理的推文ID"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('processed_ids', [])
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
        return []
    
    def _save_processed_tweets(self):
        """保存已处理的推文ID"""
        try:
            data = {
                'processed_ids': self.processed_ids[-1000:],  # 只保留最近1000条
                'last_update': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据文件失败: {e}")
    
    def _is_monitoring_time(self) -> bool:
        """检查是否在监控时间内（北京时间11:00-23:00）"""
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = datetime.now(beijing_tz)
        return 11 <= beijing_time.hour <= 23
    
    def _get_next_token(self) -> str:
        """获取下一个可用Token"""
        token = self.bearer_tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.bearer_tokens)
        return token
    
    def _make_twitter_request(self, url: str, params: Dict) -> Optional[Dict]:
        """发起Twitter API请求，自动轮换Token"""
        for attempt in range(len(self.bearer_tokens)):
            token = self._get_next_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': 'BinanceTweetMonitor/1.0'
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Token达到限制，切换到下一个Token")
                    continue
                else:
                    logger.error(f"API请求失败: {response.status_code}")
                    return None
                    
            except Exception as e:
                logger.error(f"请求异常: {e}")
                continue
        
        logger.error("所有Token都不可用")
        return None
    
    def get_user_tweets(self) -> List[Dict]:
        """获取用户推文"""
        # 先获取用户ID
        user_url = f"https://api.twitter.com/2/users/by/username/{self.target_user}"
        user_params = {'user.fields': 'id'}
        
        user_data = self._make_twitter_request(user_url, user_params)
        if not user_data or 'data' not in user_data:
            logger.error("获取用户信息失败")
            return []
        
        user_id = user_data['data']['id']
        
        # 获取推文
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        tweets_params = {
            'max_results': 10,
            'tweet.fields': 'created_at,public_metrics',
            'exclude': 'retweets,replies'
        }
        
        tweets_data = self._make_twitter_request(tweets_url, tweets_params)
        if tweets_data and 'data' in tweets_data:
            return tweets_data['data']
        
        return []
    
    def contains_alpha_keywords(self, text: str) -> bool:
        """检查是否包含Alpha关键词"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.alpha_keywords)
    
    def send_wechat_message(self, content: str) -> bool:
        """发送企业微信消息"""
        if not self.wechat_webhook:
            logger.warning("未配置微信webhook")
            return False
        
        try:
            data = {
                "msgtype": "text",
                "text": {"content": content}
            }
            
            response = requests.post(
                self.wechat_webhook,
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
            
        except Exception as e:
            logger.error(f"发送微信消息异常: {e}")
        
        return False
    
    def format_message(self, tweet: Dict) -> str:
        """格式化推文消息"""
        beijing_tz = timezone(timedelta(hours=8))
        tweet_time = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
        beijing_time = tweet_time.astimezone(beijing_tz)
        
        tweet_url = f"https://twitter.com/{self.target_user}/status/{tweet['id']}"
        
        return f"""🚀 币安Alpha积分推文提醒

📝 内容: {tweet['text']}

🕐 时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

🔗 链接: {tweet_url}

💰 #币安 #Alpha积分 #推特监控"""
    
    def run(self):
        """运行监控"""
        try:
            logger.info("开始执行推特监控")
            
            # 检查监控时间
            if not self._is_monitoring_time():
                logger.info("当前不在监控时间范围内（北京时间11:00-23:00）")
                return
            
            # 获取推文
            tweets = self.get_user_tweets()
            if not tweets:
                logger.info("未获取到推文")
                return
            
            # 处理新推文
            new_alpha_tweets = []
            for tweet in tweets:
                tweet_id = tweet['id']
                
                # 跳过已处理的推文
                if tweet_id in self.processed_ids:
                    continue
                
                # 检查是否包含Alpha关键词
                if self.contains_alpha_keywords(tweet['text']):
                    new_alpha_tweets.append(tweet)
                    logger.info(f"发现Alpha推文: {tweet_id}")
                
                # 标记为已处理
                self.processed_ids.append(tweet_id)
            
            # 发送通知
            for tweet in new_alpha_tweets:
                message = self.format_message(tweet)
                self.send_wechat_message(message)
                time.sleep(2)  # 避免频率限制
            
            # 保存处理记录
            self._save_processed_tweets()
            
            logger.info(f"监控完成，处理了{len(new_alpha_tweets)}条Alpha推文")
            
        except Exception as e:
            logger.error(f"监控执行失败: {e}")
            raise

def main():
    """主函数"""
    try:
        monitor = BinanceTwitterMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()
