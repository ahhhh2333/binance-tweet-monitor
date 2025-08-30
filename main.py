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
        
        # 扩展的Alpha关键词列表
        self.alpha_keywords = [
            # 基础Alpha关键词
            'alpha', 'Alpha', 'ALPHA', 'aplha', 'Aplha',
            
            # 积分相关
            '积分', 'points', 'Points', 'point', 'Point',
            
            # 空投相关
            '空投', 'airdrop', 'Airdrop', 'AIRDROP',
            'airdrops', 'Airdrops', 'AIRDROPS',
            
            # 活动相关
            '领取', 'claim', 'Claim', 'CLAIM',
            '申领', '代币空投',
            
            # 组合关键词
            'Alpha积分', 'alpha积分', 'Alpha Points', 'alpha points',
            'Alpha空投', 'alpha空投', 'ALPHA空投',
            '币安Alpha', '币安alpha', 'Binance Alpha', 'binance alpha',
            
            # 奖励相关
            '奖励', 'reward', 'Reward', 'REWARD', 'rewards'
        ]
        
        # 数据文件
        self.data_file = 'processed_tweets.json'
        self.processed_data = self._load_processed_tweets()
        
        logger.info(f"初始化完成，共{len(self.bearer_tokens)}个Token，{len(self.alpha_keywords)}个关键词")
    
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
    
    def _load_processed_tweets(self) -> Dict[str, Any]:
        """加载已处理的推文数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保数据结构正确
                    if 'processed_ids' not in data:
                        data['processed_ids'] = []
                    if 'alpha_sent_ids' not in data:
                        data['alpha_sent_ids'] = []
                    return data
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
        
        return {
            'processed_ids': [],      # 所有已处理的推文ID
            'alpha_sent_ids': [],     # 已发送过Alpha通知的推文ID
            'last_update': None
        }
    
    def _save_processed_tweets(self):
        """保存已处理的推文数据"""
        try:
            # 只保留最近1000条记录
            self.processed_data['processed_ids'] = self.processed_data['processed_ids'][-1000:]
            self.processed_data['alpha_sent_ids'] = self.processed_data['alpha_sent_ids'][-1000:]
            self.processed_data['last_update'] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, ensure_ascii=False, indent=2)
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
    
    def get_single_tweet(self, tweet_id: str) -> Optional[Dict]:
        """获取单条推文的完整内容"""
        url = f"https://api.twitter.com/2/tweets/{tweet_id}"
        params = {
            'tweet.fields': 'created_at,public_metrics,entities,context_annotations',
            'expansions': 'author_id'
        }
        
        result = self._make_twitter_request(url, params)
        if result and 'data' in result:
            return result['data']
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
        
        # 获取推文列表 - 改为5条以节省API额度
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        tweets_params = {
            'max_results': 5,
            'tweet.fields': 'created_at,public_metrics,entities,context_annotations',
            'exclude': 'retweets,replies'
        }
        
        tweets_data = self._make_twitter_request(tweets_url, tweets_params)
        if not tweets_data or 'data' not in tweets_data:
            return []
        
        # 获取每条推文的完整内容
        complete_tweets = []
        for tweet in tweets_data['data']:
            # 如果推文看起来被截断了，获取完整内容
            if len(tweet['text']) >= 275 or tweet['text'].endswith('…'):
                logger.info(f"推文 {tweet['id']} 可能被截断，获取完整内容")
                complete_tweet = self.get_single_tweet(tweet['id'])
                if complete_tweet:
                    complete_tweets.append(complete_tweet)
                else:
                    complete_tweets.append(tweet)
            else:
                complete_tweets.append(tweet)
        
        return complete_tweets
    
    def contains_alpha_keywords(self, text: str) -> List[str]:
        """检查是否包含Alpha关键词，返回匹配的关键词列表"""
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in self.alpha_keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        # 添加调试日志
        logger.info(f"检查推文: {text[:100]}...")
        if matched_keywords:
            logger.info(f"匹配到关键词: {matched_keywords}")
        else:
            logger.info("未匹配到任何关键词")
        
        return matched_keywords
    
    def send_wechat_message(self, content: str) -> bool:
        """发送企业微信消息"""
        if not self.wechat_webhook:
            logger.warning("未配置微信webhook")
            return False
        
        try:
            # 企业微信消息长度限制，如果太长就截断
            if len(content.encode('utf-8')) > 3800:
                content = content[:1800] + "\n\n...(内容较长，请点击链接查看完整内容)"
            
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
    
    def format_message(self, tweet: Dict, matched_keywords: List[str]) -> str:
        """格式化推文消息"""
        beijing_tz = timezone(timedelta(hours=8))
        tweet_time = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
        beijing_time = tweet_time.astimezone(beijing_tz)
        
        tweet_url = f"https://twitter.com/{self.target_user}/status/{tweet['id']}"
        
        # 获取完整推文内容
        full_text = tweet['text']
        
        return f"""📝 内容: {full_text}

🕐 时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)

🔗 链接: {tweet_url}"""
    
    def run(self):
        """运行监控"""
        try:
            logger.info("开始执行推特监控")
            logger.info(f"当前时间: {datetime.now()}")
            
            # 检查监控时间
            if not self._is_monitoring_time():
                logger.info("当前不在监控时间范围内（北京时间11:00-23:00）")
                return
            
            # 获取推文
            tweets = self.get_user_tweets()
            if not tweets:
                logger.info("未获取到推文")
                return
            
            logger.info(f"获取到 {len(tweets)} 条推文")
            
            # 处理新推文
            new_alpha_tweets = []
            for tweet in tweets:
                tweet_id = tweet['id']
                tweet_text = tweet['text']
                
                logger.info(f"检查推文 {tweet_id}: {tweet_text[:50]}...")
                
                # 检查是否包含Alpha关键词
                matched_keywords = self.contains_alpha_keywords(tweet_text)
                
                if matched_keywords:
                    # 检查是否已经发送过Alpha通知
                    if tweet_id in self.processed_data['alpha_sent_ids']:
                        logger.info(f"推文 {tweet_id} 已发送过Alpha通知，跳过")
                    else:
                        tweet['matched_keywords'] = matched_keywords
                        new_alpha_tweets.append(tweet)
                        logger.info(f"发现Alpha推文: {tweet_id} (长度: {len(tweet_text)}字符)")
                        # 标记为已发送Alpha通知
                        self.processed_data['alpha_sent_ids'].append(tweet_id)
                else:
                    logger.info(f"推文 {tweet_id} 不包含Alpha关键词")
                
                # 标记为已处理（无论是否包含Alpha关键词）
                if tweet_id not in self.processed_data['processed_ids']:
                    self.processed_data['processed_ids'].append(tweet_id)
            
            # 按时间顺序发送通知（从旧到新）
            new_alpha_tweets.sort(key=lambda x: x['created_at'])
            
            for tweet in new_alpha_tweets:
                matched_keywords = tweet.get('matched_keywords', [])
                message = self.format_message(tweet, matched_keywords)
                self.send_wechat_message(message)
                time.sleep(3)  # 避免频率限制
            
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
