"""把帖子草稿发到 X。

需要先在 https://developer.x.com 创建 App，拿到四个密钥，
设为环境变量（或 GitHub repo secrets）：
    X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET

没有密钥时自动跳过发帖（草稿保留在 out/ 下），不会报错。
"""
import glob
import os

REQUIRED = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]


def can_post():
    return all(os.environ.get(k) for k in REQUIRED)


def post_text(text):
    from requests_oauthlib import OAuth1
    import requests

    auth = OAuth1(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = requests.post(
        "https://api.x.com/2/tweets", json={"text": text}, auth=auth, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def post_all(posts_dir, dry_run=False):
    paths = sorted(glob.glob(os.path.join(posts_dir, "*.txt")))
    if not paths:
        print("[post] 没有待发草稿。")
        return []
    if not can_post():
        print("[post] 未检测到 X_* 环境变量，跳过发帖（草稿已保留在 out/ 下）。")
        return []
    results = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            continue
        if dry_run:
            print(f"[dry-run] 将发布 {os.path.basename(path)}:\n{text}\n{'-' * 40}")
            results.append((path, "dry-run"))
            continue
        data = post_text(text)
        tweet_id = (data.get("data") or {}).get("id")
        print(f"[post] 已发布 {os.path.basename(path)} -> tweet {tweet_id}")
        results.append((path, tweet_id))
    return results
