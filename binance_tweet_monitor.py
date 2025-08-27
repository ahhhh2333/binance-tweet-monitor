#!/usr/bin/env python3
"""
binance_tweet_monitor.py
使用 8 个 Twitter Bearer Token 轮询 @binancezh，
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

# ---------- 主逻辑 ----------
def main() -> None:
    # 收集所有非空 Token（共 8 个）
    tokens = [t for t in [
        os.getenv("TWITTER_BEARER_TOKEN_1"),
        os.getenv("TWITTER_BEARER_TOKEN_2"),
        os.getenv("TWITTER_BEARER_TOKEN_3"),
        os.getenv("TWITTER_BEARER_TOKEN_4"),
        os.getenv("TWITTER_BEARER_TOKEN_5"),
        os.getenv("TWITTER_BEARER_TOKEN_6"),
        os.getenv("TWITTER_BEARER_TOKEN_7"),
        os.getenv("TWITTER_BEARER_TOKEN_8"),
    ] if t]

    if not tokens:
        print("❌ 没有任何可用的 Bearer Token，请检查 8 个 Secrets")
        return

    for idx, token in enumerate(tokens, 1):
        try:
            client = tweepy.Client(bearer_token=token)
            user = client.get_user(username=SCREEN_NAME)
            last = load_last_id()

            tweets = client.get_users_tweets(
                id=user.data.id,
                max_results=20,
                since_id=last,
                tweet_fields=["id", "text"]
            )

            if tweets.data:
                new_last = 0
                for t in reversed(tweets.data):
                    if KEYWORD in t.text.lower():
                        msg = (
                            f"【币安 Alpha 新推文】\n{t.text}\n"
                            f"https://twitter.com/{SCREEN_NAME}/status/{t.id}"
                        )
                        push_wechat(msg)
                        new_last = max(new_last, int(t.id))
                        print(f"📤 已推送：{t.id} (Token {idx})")
                if new_last:
                    save_last_id(new_last)
                    print(f"💾 更新 last_id → {new_last}")
                    return  # 成功即退出
        except Exception as e:
            print(f"⚠️  Token {idx} 失败: {e}")

    print("❌ 所有 8 个 Token 均已用完或失败")

if __name__ == "__main__":
    main()
