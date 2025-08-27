#!/usr/bin/env python3
import os, requests, tweepy

CACHE_FILE = "last_id.txt"
SCREEN_NAME = "binancezh"
KEYWORD = "alpha"

def load_last_id():
    return int(open(CACHE_FILE).read()) if os.path.exists(CACHE_FILE) else 0
def save_last_id(i):
    open(CACHE_FILE, "w").write(str(i))

def main():
    client = tweepy.Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
    user_id = client.get_user(username=SCREEN_NAME).data.id
    last = load_last_id()
    tweets = client.get_users_tweets(id=user_id, max_results=5, since_id=last,
                                    tweet_fields=["id", "text"])
    if not tweets.data:
        print("暂无新推文"); return
    new_last = 0
    for t in reversed(tweets.data):
        if KEYWORD in t.text.lower():
            msg = f"【币安 Alpha 新推文】\n{t.text}\nhttps://twitter.com/{SCREEN_NAME}/status/{t.id}"
            requests.post(os.environ["WECHAT_WEBHOOK_URL"], json={"msgtype":"text","text":{"content":msg}}, timeout=10)
            new_last = max(new_last, int(t.id))
    if new_last:
        save_last_id(new_last)
        print("已推送并更新 last_id:", new_last)

if __name__ == "__main__":
    main()
