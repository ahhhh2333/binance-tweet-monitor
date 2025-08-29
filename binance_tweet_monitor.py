#!/usr/bin/env python3
"""
binance_tweet_monitor.py
单 Token 调试版：只用 TWITTER_BEARER_TOKEN
"""
import os
import requests
import tweepy

CACHE_FILE   = "last_id.txt"
SCREEN_NAME  = "binancezh"
KEYWORD      = "alpha"

def load_last_id() -> int:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return int(f.read().strip())
    except ValueError:
        pass
    return 0

def save_last_id(tweet_id: int) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(str(tweet_id))

def push_wechat(msg: str) -> None:
    url = os.environ["WECHAT_WEBHOOK_URL"]
    payload = {"msgtype": "text", "text": {"content": msg}}
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()

def main() -> None:
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        print("❌ 没有 Bearer Token，请检查 Secrets 中的 TWITTER_BEARER_TOKEN")
        return

    print(f"🔍 使用 Token：{token[:10]}...")

    client = tweepy.Client(bearer_token=token)
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
        tweet_fields=["id", "text", "note_tweet"]
    )

    if not tweets.data:
        print("✅ 暂无新推文")
        return

    new_last = 0
    for t in reversed(tweets.data):
        full_text = t.note_tweet.text if t.note_tweet else t.text
        if KEYWORD in full_text.lower():
            msg = (
                f"【币安 Alpha 新推文】\n{full_text}\n"
                f"https://twitter.com/{SCREEN_NAME}/status/{t.id}"
            )
            push_wechat(msg)
            new_last = max(new_last, int(t.id))
            print(f"📤 已推送：{t.id}")

    if new_last:
        save_last_id(new_last)
        print(f"💾 更新 last_id → {new_last}")

if __name__ == "__main__":
    main()
