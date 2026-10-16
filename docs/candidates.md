# 候选收录 Agent 清单（2026-10-16 整理）

已收录 12 个：Claude Code、Codex、Cursor、Gemini CLI、OpenCode、GitHub Copilot、
MiniMax Code、ZCode、DeepSeek Harness、Qoder、ChatGPT & Codex、OpenClaw。

图例：✅ 建议收录　⏳ 暂缓/待验证　❌ 暂不收录

## Coding Agent（未收录）

| Agent | 厂商 | 一句话介绍 | 数据源 | 建议 |
|---|---|---|---|---|
| Cline | 开源社区 | VSCode 智能体插件鼻祖，v4.1.25（10-16 刚发），极其活跃 | GitHub Releases `cline/cline` ✅ | ✅ 强烈建议，零成本接入 |
| Kilo Code | Kilo-Org | Cline 系活跃分支，v7.8.12（10-15），迭代快 | GitHub Releases `Kilo-Org/kilocode` ✅ | ✅ 建议，零成本接入 |
| Qwen Code | 阿里 Qwen | 官方开源终端 agent，v0.25.2（10-15），活跃 | GitHub Releases `QwenLM/qwen-code` ✅ | ✅ 建议，补齐国产开源一环 |
| Kiro | AWS | spec-driven agentic IDE（IDE/CLI/Web），AWS 背书，合规性强 | 官网 changelog（kiro.dev/changelog，分 CLI/General/Models） | ✅ 建议，需写 webpage 解析器 |
| Windsurf / Devin | Cognition | 老牌 IDE agent，已并入 Devin（Cascade 被 Devin Local 取代） | docs.devin.ai 的 changelog 页面 | ✅ 建议，需写 webpage 解析器 |
| Zed | zed-industries | 开源高性能编辑器 + AI 功能，v1.25.0-pre 活跃 | GitHub Releases `zed-industries/zed` ✅ | ⏳ 可选：编辑器本体，非纯 agent |
| Aider | 开源社区 | 终端 agent 先驱 | GitHub Releases `Aider-AI/aider`，但停在 v0.86.0（2025-08） | ⏳ 暂缓：更新节奏疑似放缓，先观察 |
| Roo Code | RooCodeInc | VSCode 智能体插件 | v3.54.0（2026-05）之后 5 个月无更新 | ⏳ 暂缓 |
| Junie | JetBrains | JetBrains 官方 coding agent | JetBrains 官网 release notes（待验证） | ⏳ 数据源待验证 |
| Amp | Sourcegraph | 终端 agentic coding 工具 | changelog 待验证 | ⏳ 数据源待验证 |
| Antigravity | Google DeepMind | Google 的 agentic IDE | changelog 待验证 | ⏳ 数据源待验证 |
| CodeBuddy | 腾讯 | WorkBuddy 同门，国内影响力大 | changelog 待验证 | ⏳ 数据源待验证 |
| Comate / 灵码 | 百度 / 阿里 | 国内大厂 coding 助手 | changelog 待验证 | ⏳ 数据源待验证 |

## 通用 Agent

| Agent | 厂商 | 一句话介绍 | 数据源 | 建议 |
|---|---|---|---|---|
| ChatGPT | OpenAI | 已收录（ChatGPT & Codex changelog） | learn.chatgpt.com/docs/changelog ✅ | ✅ 已收录 |
| Manus | Manus（新加坡） | 通用 agent 标杆，9 月底发 2.0 + Cue 个人 agent | 无官方公开 changelog，只有新闻稿 | ❌ 暂不：无稳定数据源 |
| Claude（网页版） | Anthropic | claude.ai 的 agent 功能 | 无公开 changelog | ❌ 暂不 |
| Genspark / Fellou | 各家 | 通用/浏览器 agent | 无公开 changelog | ❌ 暂不 |
| Comet / Dia / Atlas | Perplexity/BC/OpenAI | AI 浏览器（agentic browsing） | 无公开 changelog | ❌ 暂不 |
| Microsoft 365 Copilot | 微软 | 企业办公 agent | 更新走 M365 Message Center，企业向 | ❌ 与账号定位不符 |

## 垂直领域 Agent

| Agent | 厂商 | 一句话介绍 | 数据源 | 建议 |
|---|---|---|---|---|
| Lovable | Lovable | AI 建站/应用生成，vibe coding 代表 | 官网 changelog（待验证） | ⏳ 可选：垂直但影响力大 |
| v0 | Vercel | AI 生成 Web 界面 | 官网 changelog（待验证） | ⏳ 可选 |
| Bolt | StackBlitz | 浏览器内全栈 AI 开发 | 官网 changelog（待验证） | ⏳ 可选 |
| Replit Agent | Replit | Replit 的 agent 开发模式 | replit 官网 changelog（待验证） | ⏳ 可选 |
| Harvey 等法律/医疗 agent | 各家 | 高度垂直 | 多无公开 changelog，且偏离定位 | ❌ 暂不 |

## 优先级建议

1. **立刻加（零成本）**：Cline、Kilo Code、Qwen Code —— 都是 GitHub Releases，改一行配置的事。
2. **下个迭代**：Kiro、Windsurf/Devin —— 影响力大，但各需一个 webpage 解析器。
3. **先放着**：Aider、Roo Code（等更新节奏恢复）；Manus 等通用 agent（等官方出 changelog）。
