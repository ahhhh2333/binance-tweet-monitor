#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter API v2 管理器 - 支持多token轮换
"""

import time
import json
import os
import requests
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class TwitterAPIManager:
    """Twitter API v2 管理器 - 支持多token轮换"""
    
    def __init__(self, bearer_tokens: List[str]):
        self.bearer_tokens = bearer_tokens
        self.current_token_index = 0
        self.token_usage_file = 'data/token_usage.json'
        self.token_usage = self._load_token_usage()
        
        # Twitter API v2 端点
        self.base_url = "https://api.twitter.com/2"
        
        logger.info(f"初始化Twitter API管理器，共 {len(self.bearer_tokens)} 个token")
    
    def _load_token_usage(self) -> Dict[str, Any]:
        """加载token使用记录"""
        try:
            if os.path.exists(self.token_usage_file):
                with open(self.token_usage_file, 'r') as f:
                    data = json.load(f)
                    # 清理过期记录
                    current_time = time.time()
                    for token_idx in data:
                        if 'requests' in data[token_idx]:
                            data[token_idx]['requests'] = [
                                req for req in data[token_idx]['requests']
                                if current_time - req < 900  # 15分钟窗口
                            ]
                    return data
        except Exception as e:
            logger.error(f"加载token使用记录失败: {e}")
        return {}
    
    def _save_token_usage(self):
        """保存token使用记录"""
        try:
            os.makedirs(os.path.dirname(self.token_usage_file), exist_ok=True)
            with open(self.token_usage_file, 'w') as f:
                json.dump(self.token_usage, f)
        except Exception as e:
            logger.error(f"保存token使用记录失败: {e}")
    
    def _get_current_token(self) -> str:
        """获取当前可用的token"""
        return self.bearer_tokens[self.current_token_index]
    
    def _can_use_token(self, token_index: int) -> bool:
        """检查指定token是否可用"""
        token_key = str(token_index)
        if token_key not in self.token_usage:
            self.token_usage[token_key] = {'requests': [], 'last_error': None}
        
        current_time = time.time()
        # 清理过期记录
        self.token_usage[token_key]['requests'] = [
            req for req in self.token_usage[token_key]['requests']
            if current_time - req < 900  # 15分钟窗口
        ]
        
        # Twitter API v2免费版：每15分钟100次请求
        return len(self.token_usage[token_key]['requests']) < 90  # 保留一些缓冲
    
    def _record_token_usage(self, token_index: int, success: bool = True, error: Optional[str] = None):
        """记录token使用情况"""
        token_key = str(token_index)
        if token_key not in self.token_usage:
            self.token_usage[token_key] = {'requests': [], 'last_error': None}
        
        if success:
            self.token_usage[token_key]['requests'].append(time.time())
            self.token_usage[token_key]['last_error'] = None
        else:
            self.token_usage[token_key]['last_error'] = {
                'time': time.time(),
                'error': error
            }
        
        self._save_token_usage()
    
    def _switch_to_next_token(self):
        """切换到下一个可用token"""
        original_index = self.current_token_index
        
        # 尝试找到可用的token
        for i in range(len(self.bearer_tokens)):
            test_index = (self.current_token_index + i) % len(self.bearer_tokens)
            if self._can_use_token(test_index):
                self.current_token_index = test_index
                if test_index != original_index:
                    logger.info(f"切换到token {test_index + 1}/{len(self.bearer_tokens)}")
                return True
        
        logger.warning("所有token都已达到限制，等待重置")
        return False
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """发起API请求，自动处理token轮换"""
        max_retries = len(self.bearer_tokens)
        
        for attempt in range(max_retries):
            if not self._switch_to_next_token():
                logger.error("所有token都不可用")
                return None
            
            current_token = self._get_current_token()
            headers = {
                'Authorization': f'Bearer {current_token}',
                'User-Agent': 'BinanceTweetMonitorBot/2.0'
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    self._record_token_usage(self.current_token_index, success=True)
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Token {self.current_token_index + 1} 达到速率限制")
                    self._record_token_usage(self.current_token_index, success=False, error="Rate limit")
                    # 尝试下一个token
                    continue
                elif response.status_code == 401:
                    logger.error(f"Token {self.current_token_index + 1} 认证失败")
                    self._record_token_usage(self.current_token_index, success=False, error="Unauthorized")
                    continue
                else:
                    logger.error(f"API请求失败: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                logger.error(f"请求异常: {e}")
                continue
        
        logger.error("所有token重试失败")
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息"""
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            'user.fields': 'id,name,username,public_metrics'
        }
        
        response = self._make_request(url, params)
        return response.get('data') if response else None
    
    def get_user_tweets(self, user_id: str, since_id: Optional[str] = None, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """获取用户推文"""
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,public_metrics,context_annotations,entities',
            'exclude': 'retweets,replies'
        }
        
        if since_id:
            params['since_id'] = since_id
        
        response = self._make_request(url, params)
        if response and 'data' in response:
            return response['data']
        elif response and 'errors' in response:
            logger.error(f"获取推文出错: {response['errors']}")
        
        return []
    
    def get_token_status(self) -> Dict[str, Any]:
        """获取所有token的状态"""
        status = {}
        for i, token in enumerate(self.bearer_tokens):
            masked_token = token[:10] + '...' + token[-4:] if len(token) > 14 else token
            status[f"token_{i+1}"] = {
                'masked_token': masked_token,
                'can_use': self._can_use_token(i),
                'usage_count': len(self.token_usage.get(str(i), {}).get('requests', [])),
                'last_error': self.token_usage.get(str(i), {}).get('last_error')
            }
        return status