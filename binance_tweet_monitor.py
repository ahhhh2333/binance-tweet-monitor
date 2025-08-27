#!/usr/bin/env python3
import os, random, time, requests, tweepy

CACHE_FILE   = "last_id.txt"
SCREEN_NAME  = "binancezh"
KEYWORD      = "alpha"

# 所有 Bearer Token（按顺序）
TOKENS = [
    os.getenv("TWITTER_BEARER_TOKEN_1"),
    os.getenv("TWITTER_BEARER_TOKEN_2"),
    # 继续加 3、4…
]

def load_last_id():
    return int(open(CACHE_FILE).read()) if os.path.exists(CACHE_FILE) else 0
def save_last_id(i):
    open(CACHE_FILE, "w").write(str(i))

def try_one_token(token):
    client = tweepy.Client(bearer_token=token)
    user   = client.get_user(username=SCREEN_NAME)
    last   = load_last_id()
    tweets = client.get_users_tweets(id=user.data.id, max_results=20, since_id=last,
                                     tweet_fields=["id","text"])
    if not tweets.data:
        return False
    sent = 0
    for t in reversed(tweets.data):
        if KEYWORD in t.text.lower():
            msg = f"【币安 Alpha 新推文】\n{t.text}\nhttps://twitter.com/{SCREEN_NAME}/status/{t.id}"
            requests.post(os.getenv("WECHAT_WEBHOOK_URL"), json={"msgtype":"text","text":{"content":msg}}, timeout=10)
            sent += 1
            save_last_id(int(t.id))
    return sent > 0

def main():
    random.shuffle(TOKENS)          # 每次随机起点，防止热点
    for tk in TOKENS:
        if tk and try_one_token(tk):
            print(f"✅ 使用 {tk[:10]}... 推送成功")
            return
        else:
            print(f"⚠️  {tk[:10]}... 已用完或失败，尝试下一个")
    print("❌ 所有 Token 都用尽，本次跳过")

if __name__ == "__main__":
    main()
