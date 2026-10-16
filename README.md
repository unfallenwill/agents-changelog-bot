# agentschangelog-bot 🤖📰

[@agentschangelog](https://x.com/agentschangelog) 背后的机器人：
每天自动抓取各家 AI coding agent 的 changelog，有新版本就生成 X 帖子草稿并发布。

## 收录的 agent

| Agent | 数据源 |
|---|---|
| Claude Code | 官方 Atom 订阅（`anthropics/claude-code` 的 `feed.xml`） |
| OpenAI Codex | GitHub Releases（`openai/codex`） |
| Cursor | 官方 RSS（`cursor.com/changelog/rss.xml`） |
| OpenCode | GitHub Releases（`anomalyco/opencode`，1.x 稳定线） |
| GitHub Copilot | GitHub 官方 changelog RSS（按 `copilot` 关键词过滤） |
| MiniMax Code | GitHub Releases（`MiniMax-AI/minimax-code`） |
| ZCode | GitHub Releases（`zai-org/ZCode`） |
| DeepSeek Harness | GitHub Releases（`deepseek-ai/deepseek-harness`，含 alpha 预览版） |
| Qoder | 官网 Release Notes 页面解析（`docs.qoder.com/release-notes/qoder`） |
| ChatGPT & Codex | OpenAI 官方 changelog 页面解析（`learn.chatgpt.com/docs/changelog`） |
| OpenClaw | GitHub Releases（`openclaw/openclaw`） |
| Cline | GitHub Releases（`cline/cline`） |
| Kilo Code | GitHub Releases（`Kilo-Org/kilocode`） |
| Devin | Devin Docs changelog 页面解析（`docs.devin.ai/desktop/changelog`，原 Windsurf） |

新增 agent 只需在 `agents.yaml` 里加一段配置：
`github_releases` / `feed` 类型无需改代码；
`webpage` 类型需要在 `fetcher.py` 里加一个对应站点的解析函数。

## 本地运行

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 只检查新增（不改 state、不写文件）
.venv/bin/python main.py --check

# 生成日报 + 帖子草稿，并更新 data/state.json
.venv/bin/python main.py --digest

# 预览要发的帖子（不真正发布）
.venv/bin/python main.py --post --dry-run
```

- `data/state.json` 记录每个源已见过的条目，首次运行只建基线、不发帖。
- 日报和草稿输出到 `out/<日期>/`（已 gitignore，不进仓库）。

## 定时任务（GitHub Actions）

`.github/workflows/changelog.yml` 每天 09:00（北京时间）自动运行：
抓取 → 生成草稿 → 发到 X → 把 `data/state.json` 回写到仓库。

## 要点提炼：规则版 / LLM 版

默认是纯规则提炼（取正文前几行），零成本、零密钥。
如需让模型挑出"最值得关注"的 1-2 条，可选配 LLM（`summarizer.py`，
OpenAI 兼容接口，失败自动回退到规则版）：

| Secret | 说明 | 默认值 |
|---|---|---|
| `LLM_API_KEY` | 有它才启用，不配就不走 LLM | （未启用） |
| `LLM_API_BASE` | 接口地址 | `https://api.groq.com/openai/v1` |
| `LLM_MODEL` | 模型 | `openai/gpt-oss-120b` |
| `SUMMARY_LANG` | 摘要语言 `zh`/`en` | `zh` |

免费额度参考（2026-10 核实，会变）：Groq 免费约 1000 请求/天（`gpt-oss-120b` 等，
无需绑卡）；Gemini API Flash 系列免费约 1500 请求/天。本项目一天只跑一次、
几十次请求，免费额度绰绰有余。

## 接入 X 发帖

1. 在 https://developer.x.com 创建 App，拿到 4 个密钥：
   `X_API_KEY`、`X_API_SECRET`、`X_ACCESS_TOKEN`、`X_ACCESS_TOKEN_SECRET`
   （Access Token 需开启 Read and Write 权限）
2. 在 GitHub 仓库 Settings → Secrets → Actions 里添加这 4 个 secret。
3. 没有配密钥时发帖步骤会自动跳过，只保留草稿，不会报错。

免费档 API 即可发帖（每月有条数上限，具体以 X 开发者文档为准）。

## 发到 GitHub

```bash
cd agentschangelog-bot
git init && git add -A && git commit -m "init: agentschangelog-bot"
gh repo create agentschangelog-bot --public --source=. --push
```

之后 Actions 会按定时自动跑起来。
