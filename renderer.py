"""把新增条目渲染成 X 帖子草稿和日报 markdown。"""
import os
import re
from datetime import date

from summarizer import summarize_bullets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "out")

MAX_POST_LEN = 280  # 帖子正文上限（X 单条上限），保持简洁


def _fit(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 0)].rstrip() + "…"


def _first_bullets(body, max_chars=320, max_lines=4):
    """从 changelog 正文里提炼前几个要点。"""
    picked, total = [], 0
    for raw in (body or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^[-*•·\d.)\s`>]+", "", line).strip()
        line = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", line)  # 去掉 markdown 链接
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line).strip()  # 去掉加粗
        if len(line) < 8:
            continue
        if "|" in line:
            continue  # 跳过 "中文 | English" 这类语言切换行和 markdown 表格行
        if total + len(line) > max_chars:
            # 这一条放不下：如果一条都还没选，截断这一条放进去
            if not picked:
                room = max_chars - 4  # "• " 前缀 + "…" 后缀
                if room > 20:
                    picked.append("• " + line[:room].rstrip() + "…")
            break
        picked.append("• " + line)
        total += len(line)
        if len(picked) >= max_lines:
            break
    return "\n".join(picked)


def render_post(agent, item):
    """渲染单条 X 帖子（纯文本，尽量控制在 MAX_POST_LEN 内）。"""
    name = agent["name"]
    version = (item.get("version") or "").strip()
    title = (item.get("title") or "").strip()
    url = item.get("url") or ""
    tag = agent.get("hashtag") or ""

    head = f"🆕 {name} {version}".strip()
    tail = f"🔗 {url}" + (f"\n{tag}" if tag else "")
    budget = MAX_POST_LEN - len(head) - len(tail) - 4  # 留出两个空行

    middle = ""
    # 标题如果已包含在 head 里、或是版本号的另一种写法，就不再重复
    ver_variants = {version, version.lstrip("v"), "v" + version.lstrip("v")} - {""}
    if title and title not in head and not any(v in title for v in ver_variants):
        middle = title
    rest = max(budget - len(middle) - 1, 0)
    # 优先用 LLM 提炼要点（需配 LLM_API_KEY），失败或未启用则回退到规则版
    bullets = (summarize_bullets(name, title, version, item.get("body", ""),
                                 max_chars=rest)
               or _first_bullets(item.get("body", ""), max_chars=rest))
    if bullets:
        middle = f"{middle}\n{bullets}".strip() if middle else bullets
    middle = _fit(middle, max(budget, 0))

    parts = [head]
    if middle:
        parts.append(middle)
    parts.append(tail)
    return "\n\n".join(parts)


def render_digest(day, updates):
    """渲染日报 markdown：updates 为 [(agent, [items...]), ...]。"""
    lines = [f"# Agent Changelog 日报 · {day}", ""]
    for agent, items in updates:
        lines.append(f"## {agent['name']}")
        lines.append("")
        for it in items:
            title = it.get("title") or it.get("version") or "(未命名版本)"
            lines.append(f"- [{title}]({it['url']})")
            bullets = _first_bullets(it.get("body", ""), max_chars=500, max_lines=5)
            if bullets:
                lines.append("")
                for b in bullets.splitlines():
                    lines.append("  " + b.replace("• ", "- ", 1))
                lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(day, updates):
    """写出日报和帖子草稿，返回 (digest_path, [(agent_id, post_path)])。"""
    day_dir = os.path.join(OUT_DIR, day)
    posts_dir = os.path.join(day_dir, "posts")
    os.makedirs(posts_dir, exist_ok=True)

    digest_path = os.path.join(day_dir, "digest.md")
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(render_digest(day, updates))

    post_files = []
    for agent, items in updates:
        # 一个 agent 一天可能多条更新：合并成一条帖子，避免刷屏
        if len(items) == 1:
            text = render_post(agent, items[0])
        else:
            versions = ", ".join(i.get("version") or i.get("title") for i in items)
            merged = dict(items[0])
            merged["title"] = f"{len(items)} 个新版本：{versions}"
            merged["body"] = "\n".join(i.get("body", "") for i in items)
            text = render_post(agent, merged)
        path = os.path.join(posts_dir, f"{agent['id']}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        post_files.append((agent["id"], path))
    return digest_path, post_files


def today_str():
    return date.today().isoformat()
