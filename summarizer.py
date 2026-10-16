"""可选的 LLM 摘要：从 changelog 正文里挑出最值得关注的 1-2 条。

通过 OpenAI 兼容接口调用，方便接入各类免费额度：
  - Groq（推荐）：https://api.groq.com/openai/v1，模型如 openai/gpt-oss-120b；
    免费约 30 RPM / 1000 请求每天 / 20 万 token 每天，无需绑卡
    （额度 2026-10-07 核实，会变，以官方文档为准）
  - Gemini API：https://generativelanguage.googleapis.com/v1beta/openai/，
    Flash 系列免费约 1500 请求每天
  - OpenRouter :free 模型 / NVIDIA NIM / Zhipu 等也都是 OpenAI 兼容接口

环境变量（GitHub Actions 里配成 Secrets，可选）：
  LLM_API_KEY    有它才启用；没配就走纯规则提炼，不报错
  LLM_API_BASE   默认为 Groq
  LLM_MODEL      默认为 openai/gpt-oss-120b
  SUMMARY_LANG   摘要语言，zh 或 en，默认 zh

调用失败（超时、429、配错 key 等）一律返回 None，调用方回退到规则版。
"""
import os
import re

import requests

API_KEY = os.environ.get("LLM_API_KEY", "").strip()
API_BASE = os.environ.get("LLM_API_BASE",
                          "https://api.groq.com/openai/v1").rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
SUMMARY_LANG = os.environ.get("SUMMARY_LANG", "zh").strip().lower()
TIMEOUT = 30


def enabled():
    """是否配置了 LLM（配了 key 才启用）。"""
    return bool(API_KEY)


def _prompt(agent_name, title, version, body):
    lang_line = "用简体中文" if SUMMARY_LANG == "zh" else "in English"
    head = f"{agent_name} {version}".strip()
    if title and title not in head:
        head += f"：{title}"
    return (
        "你是一个 changelog 提炼助手。下面是一段软件更新说明，"
        f"请{lang_line}挑出其中最值得关注的 1 到 2 条变化，"
        "写成要点列表，每条一行、不超过 60 字，不要编号，直接给内容，"
        "不要寒暄、不要解释。只输出要点本身。\n\n"
        f"【{head}】\n{body}"
    )


def summarize_bullets(agent_name, title, version, body, max_chars=200):
    """返回 "• xxx\n• xxx"；未启用或失败时返回 None。"""
    if not enabled() or not (body or "").strip():
        return None
    # 输入截断，省 token：摘要不需要全文
    body_in = (body or "").strip()[:3000]
    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user",
                     "content": _prompt(agent_name, title, version, body_in)}
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

    lines = []
    for raw in text.splitlines():
        line = re.sub(r"^[-*•·\d.)\s`>]+", "", raw.strip()).strip()
        if len(line) >= 4:
            lines.append("• " + line)
        if len(lines) >= 2:
            break
    if not lines:
        return None
    out = "\n".join(lines)
    if len(out) > max_chars + 20:
        return None
    return out
