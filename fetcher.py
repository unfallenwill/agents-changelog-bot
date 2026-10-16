"""从各数据源抓取 changelog 条目。

支持两种来源（见 agents.yaml）：
- github_releases：GitHub Releases API
- feed：Atom / RSS 订阅

每个条目统一为 dict：
    {uid, title, version, body, url, published, prerelease}
按发布时间倒序排列（最新的在前）。
"""
import html as html_lib
import re

import feedparser
import requests

GITHUB_API = "https://api.github.com"
TIMEOUT = 30
USER_AGENT = "agentschangelog-bot/1.0"


def _github_headers(token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_github_releases(repo, token=None, limit=10,
                          include_prerelease=False, strip_prefix=""):
    """抓取 GitHub 仓库的 releases（默认跳过 draft 和 prerelease）。"""
    url = f"{GITHUB_API}/repos/{repo}/releases"
    resp = requests.get(url, headers=_github_headers(token),
                        params={"per_page": limit}, timeout=TIMEOUT)
    resp.raise_for_status()
    items = []
    for rel in resp.json():
        if rel.get("draft"):
            continue
        if rel.get("prerelease") and not include_prerelease:
            continue
        tag = rel.get("tag_name") or ""
        version = tag
        if strip_prefix and version.startswith(strip_prefix):
            version = version[len(strip_prefix):]
        items.append({
            "uid": f"github:{repo}:{rel['id']}",
            "title": rel.get("name") or tag,
            "version": version,
            "body": (rel.get("body") or "").strip(),
            "url": rel.get("html_url") or "",
            "published": rel.get("published_at") or "",
            "prerelease": bool(rel.get("prerelease")),
        })
    return items


def _clean_html(raw):
    # 块级标签先转成占位符保留条目结构；标签内的源码换行则压成空格
    text = re.sub(r"</(p|div|li|ul|ol|h\d|br|tr|table)[^>]*>", "\u0000",
                  raw or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t\r\n]+", " ", text)
    lines = [ln.strip() for ln in text.split("\u0000")]
    return "\n".join(ln for ln in lines if ln)


_VERSION_RE = re.compile(r"v?\d+\.\d+(?:\.\d+)?")
# 严格模式：版本号前必须有 app/v/version 前缀，避免把 "GPT-5.5" 这类误判成版本
_STRICT_VERSION_RE = re.compile(
    r"(?:app|v|version)\s+(v?\d+\.\d+(?:\.\d+)?)", re.I)


def _guess_version(title, strict=False):
    pat = _STRICT_VERSION_RE if strict else _VERSION_RE
    m = pat.search(title or "")
    return m.group(1) if strict and m else (m.group(0) if m else "")


def _strip_headings(content_html):
    """去掉 h1-h6 小节标题（如 "Features"/"Improvements"），只保留正文条目。"""
    return re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", content_html, flags=re.S | re.I)


def fetch_feed(url, limit=10):
    """抓取 Atom / RSS 订阅。"""
    parsed = feedparser.parse(url, agent=USER_AGENT)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"feed 解析失败: {url} ({parsed.bozo_exception})")
    items = []
    for entry in parsed.entries[:limit]:
        uid = entry.get("id") or entry.get("link") or entry.get("title")
        content = entry.get("content")
        if content:
            body = content[0].get("value", "")
        else:
            body = entry.get("summary") or entry.get("description") or ""
        if "<" in body:
            body = _clean_html(body)
        title = entry.get("title", "")
        items.append({
            "uid": str(uid),
            "title": title,
            "version": _guess_version(title),
            "body": body.strip(),
            "url": entry.get("link", ""),
            "published": entry.get("published") or entry.get("updated") or "",
            "prerelease": False,
        })
    return items


def fetch_qoder(url="https://docs.qoder.com/release-notes/qoder", limit=10):
    """抓取 Qoder 官方 Release Notes 页面（docs.qoder.com/release-notes/qoder）。

    页面结构：每个条目由 update-label（日期）/ update-description（版本号）/
    update-content（正文 HTML）三部分组成，按时间倒序排列。
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    label_pat = re.compile(r'data-component-part="update-label">([^<]+)</div>')
    matches = list(label_pat.finditer(html))
    items = []
    for idx, m in enumerate(matches[:limit]):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(html)
        chunk = html[m.start():end]
        date = m.group(1).strip()

        dm = re.search(r'data-component-part="update-description">([^<]+)</div>', chunk)
        title = dm.group(1).strip() if dm else ""

        cm = re.search(r'data-component-part="update-content">(.*)', chunk, re.S)
        content_html = cm.group(1) if cm else ""
        body = _clean_html(_strip_headings(content_html))

        am = re.search(r'<a id="([^"]+)"', chunk)
        anchor = am.group(1) if am else ""

        items.append({
            "uid": f"qoder:{title}",
            "title": title,
            "version": _guess_version(title),
            "body": body,
            "url": url + (f"#{anchor}" if anchor else ""),
            "published": date,
            "prerelease": False,
        })
    return items


def fetch_learn_chatgpt_changelog(url="https://learn.chatgpt.com/docs/changelog",
                                    limit=15):
    """抓取 OpenAI 官方「ChatGPT & Codex changelog」（learn.chatgpt.com/docs/changelog）。

    页面结构：每个条目是一个 <li id="...">，内含 <time>（日期）、
    <h3><span>（标题）、<article>（正文 HTML），按时间倒序排列。
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    starts = [m.start() for m in re.finditer(r'<li id="', html)]
    items = []
    for idx, s in enumerate(starts):
        if len(items) >= limit:
            break
        chunk = html[s:starts[idx + 1] if idx + 1 < len(starts) else len(html)]

        im = re.search(r'<li id="([^"]+)"', chunk)
        li_id = im.group(1) if im else ""
        tm = re.search(r"<time[^>]*>([^<]+)</time>", chunk)
        date = tm.group(1).strip() if tm else ""
        hm = re.search(r"<h3[^>]*>\s*<span[^>]*>(.*?)</span>", chunk, re.S)
        title = _clean_html(hm.group(1)).strip() if hm else ""
        am = re.search(r"<article[^>]*>(.*?)</article>", chunk, re.S)
        body = _clean_html(_strip_headings(am.group(1))) if am else ""
        if not title or not li_id:
            continue

        items.append({
            "uid": f"learn-chatgpt:{li_id}",
            "title": title,
            # 严格模式：只有 "Codex app 26.1007" 这类才提取版本，
            # "GPT-5.5 retirement" 这种标题不提取
            "version": _guess_version(title, strict=True),
            "body": body,
            "url": url + f"#{li_id}",
            "published": date,
            "prerelease": False,
        })
    return items


def fetch_devin_changelog(url="https://docs.devin.ai/desktop/changelog", limit=10):
    """抓取 Devin Docs 的 Devin Desktop（Windsurf）changelog。

    Mintlify 风格页面：每个条目依次包含
      data-component-part="update-label"（版本号，如 v3.10.67）
      data-component-part="update-description"（日期）
      data-component-part="update-content"（正文 HTML）
    按版本倒序排列。
    """
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    starts = [m.start() for m in re.finditer(r'data-component-part="update-label"',
                                             html)]
    items = []
    for idx, s in enumerate(starts):
        if len(items) >= limit:
            break
        chunk = html[s:starts[idx + 1] if idx + 1 < len(starts) else len(html)]

        lm = re.search(r'data-component-part="update-label">(.*?)</button>', chunk)
        version = _clean_html(lm.group(1)).strip() if lm else ""
        dm = re.search(r'data-component-part="update-description">(.*?)</div>',
                       chunk)
        date = _clean_html(dm.group(1)).strip() if dm else ""
        cm = re.search(r'data-component-part="update-content">(.*)', chunk, re.S)
        content_html = cm.group(1) if cm else ""
        # 条目开头的 <span><strong>产品名</strong></span> 拿出来做小标题
        tm = re.search(r"<span[^>]*>\s*<strong>(.*?)</strong>\s*</span>",
                       content_html, re.S)
        title = _clean_html(tm.group(1)).strip() if tm else ""
        content_html = re.sub(r"<span[^>]*>\s*<strong>.*?</strong>\s*</span>",
                              "", content_html, count=1, flags=re.S)
        body = _clean_html(_strip_headings(content_html))
        if not version or not body:
            continue

        items.append({
            "uid": f"devin:{version}:{date}",
            "title": title,
            "version": version,
            "body": body,
            "url": url,
            "published": date,
            "prerelease": False,
        })
    return items


def fetch_agent(agent, token=None):
    """按 agents.yaml 中的配置抓取单个 agent 的 changelog。"""
    source = agent.get("source", {})
    kind = source.get("type")
    if kind == "github_releases":
        return fetch_github_releases(
            source["repo"],
            token=token,
            include_prerelease=source.get("include_prerelease", False),
            strip_prefix=source.get("strip_prefix", ""),
        )
    if kind == "feed":
        return fetch_feed(source["url"])
    if kind == "webpage":
        parser = source.get("parser")
        if parser == "qoder":
            return fetch_qoder(source["url"])
        if parser == "learn-chatgpt-changelog":
            return fetch_learn_chatgpt_changelog(source["url"])
        if parser == "devin-changelog":
            return fetch_devin_changelog(source["url"])
        raise ValueError(f"未知的 webpage 解析器: {parser}")
    raise ValueError(f"未知的数据源类型: {kind}")
