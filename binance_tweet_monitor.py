#!/usr/bin/env python3
"""
binance_tweet_monitor.py
使用多个 Twitter Bearer Token 轮询 @binancezh，
仅推送含关键词“alpha”且真正未推送过的新推文。
"""
import os
import requests
import tweepy

CACHE_FILE   = "last_id.txt"
SCREEN_NAME  = "binancezh"
KEYWORD      = "alpha"          # 大小写不敏感

# ---------- 工具函数 ----------
def load_last_id() -> int:
    """读取上一次已推送的最新推文 ID"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return int(f.read().strip())
    except ValueError:
        pass
    return 0

def save_last_id(tweet_id: int) -> None:
    """记录最新已推送推文 ID"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(str(tweet_id))

def push_wechat(msg: str) -> None:
    """发送到企业微信机器人"""
    url = os.environ["WECHAT_WEBHOOK_URL"]
    payload = {"msgtype": "text", "text": {"content": msg}}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()

# ---------- 主逻辑 ----------
def main() -> None:
    # 1. 收集所有非空 Token
    tokens = [t for t in [
        os.getenv("TWITTER_BEARER_TOKEN_1"),
        os.getenv("TWITTER_BEARER_TOKEN_2"),
        os.getenv("TWITTER_BEARER_TOKEN_3"),
        # 继续按需补充
    ] if t]

    if not tokens:
        print("❌ 没有任何可用的 Bearer Token，请检查 Secrets")
        return

    # 2. 单次运行只用第一个有效 Token
    client = tweepy.Client(bearer_token=tokens[0])

    user = client.get_user(username=SCREEN_NAME)
    if not user.data:
        print("❌ 无法获取用户")
        return
    user_id = user.data.id

    last_id = load_last_id()

    tweets = client.get_users_tweets(
        id=user_id,
        max_results=20,
        since_id=last_id,
        tweet_fields=["id", "text"]
    )

    if not tweets.data:
        print("✅ 暂无新推文")
        return

    new_last = 0
    for tweet in reversed(tweets.data):
        if KEYWORD in tweet.text.lower():
            msg = (
                f"【币安 Alpha 新推文】\n{tweet.text}\n"
                f"https://twitter.com/{SCREEN_NAME}/status/{tweet.id}"
            )
            push_wechat(msg)
            new_last = max(new_last, int(tweet.id))
            print(f"📤 已推送：{tweet.id}")

    if new_last:
        save_last_id(new_last)
        print(f"💾 更新 last_id → {new_last}")

if __name__ == "__main__":
    main()
