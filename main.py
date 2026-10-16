#!/usr/bin/env python3
"""agentschangelog-bot 入口。

用法：
    python main.py --check        只检查新增（不改 state、不写文件）
    python main.py --digest       生成日报 + 帖子草稿，并更新 state
    python main.py --post         把 out/<今天>/posts/*.txt 发到 X
    python main.py --post --dry-run   预览要发的内容，不真正发布
"""
import argparse
import os
import sys
from datetime import date

import yaml

from fetcher import fetch_agent
from renderer import render_post, write_outputs, today_str
from state import load_state, save_state
from xpost import post_all

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_agents():
    with open(os.path.join(BASE_DIR, "agents.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)["agents"]


def collect(token=None):
    """抓取全部 agent，返回 (updates, state, is_first_run)。

    updates: [(agent, [new_items...]), ...]，items 按旧→新排序。
    """
    agents = load_agents()
    state = load_state()
    is_first_run = not state
    updates = []

    for agent in agents:
        aid = agent["id"]
        try:
            items = fetch_agent(agent, token=token)
        except Exception as e:  # noqa: BLE001 - 单个源失败不影响其他
            print(f"[warn] {aid} 抓取失败: {e}", file=sys.stderr)
            continue

        keyword = (agent.get("filter_keyword") or "").lower()
        new_items = []
        for it in items:
            if it["uid"] in state.get(aid, []):
                continue
            if keyword and keyword not in (it["title"] + " " + it["body"]).lower():
                continue
            new_items.append(it)

        if new_items:
            updates.append((agent, list(reversed(new_items))))  # 旧 → 新

        # 记录本次看到的全部 uid（只记前 20 个，防止文件无限膨胀）
        state[aid] = [it["uid"] for it in items[:20]]
        print(f"[ok] {aid}: 抓到 {len(items)} 条，新增 {len(new_items)} 条")

    return updates, state, is_first_run


def cmd_check(args):
    updates, _, _ = collect(token=os.environ.get("GITHUB_TOKEN"))
    if not updates:
        print("\n没有新增。")
        return
    print()
    for agent, items in updates:
        print(f"== {agent['name']}（新增 {len(items)}）==")
        for it in items:
            print(render_post(agent, it))
            print("-" * 40)


def cmd_digest(args):
    updates, state, is_first_run = collect(token=os.environ.get("GITHUB_TOKEN"))
    save_state(state)
    if is_first_run:
        print("\n首次运行：已建立基线（state.json），不生成帖子，避免把历史版本全发一遍。")
        print("之后每次运行只会处理真正的新版本。")
        return
    if not updates:
        print("\n没有新增，state 已更新。")
        return
    day = today_str()
    digest_path, post_files = write_outputs(day, updates)
    print(f"\n日报已生成: {digest_path}")
    for aid, path in post_files:
        print(f"草稿: {path}")


def cmd_post(args):
    day = args.date or date.today().isoformat()
    posts_dir = os.path.join(BASE_DIR, "out", day, "posts")
    if not os.path.isdir(posts_dir):
        print(f"[post] 找不到 {posts_dir}，先运行 python main.py --digest 生成草稿。")
        return
    post_all(posts_dir, dry_run=args.dry_run)


def main():
    parser = argparse.ArgumentParser(description="agentschangelog-bot")
    parser.add_argument("--check", action="store_true", help="只检查新增")
    parser.add_argument("--digest", action="store_true", help="生成日报 + 草稿并更新 state")
    parser.add_argument("--post", action="store_true", help="发布草稿到 X")
    parser.add_argument("--dry-run", action="store_true", help="配合 --post：只预览不发布")
    parser.add_argument("--date", default=None, help="配合 --post：指定日期目录 YYYY-MM-DD")
    args = parser.parse_args()

    if args.digest:
        cmd_digest(args)
    elif args.post:
        cmd_post(args)
    else:
        cmd_check(args)


if __name__ == "__main__":
    main()
