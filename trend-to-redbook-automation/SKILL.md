---
name: trend-to-redbook-automation
description: 全链路搬运总控面板。将 Twitter (X) 和海外 News 新闻源，通过 MCP 服务拉取后，自动进行去毒合规、爆款文案改写，并调用本地渲染引擎一键直发小红书。此技能为端到端工作流编排器。
---

# 热点到小红书全自动搬运工作流 (Trend to Redbook Automation)

## 核心定义
这是一个**“工作流编排总指挥 (Orchestrator)”**。它本身不直接干活，而是负责在这 4 个车间之间进行调度，构成一条无代码的 AI 自动化流水线。

## 必备前置组件 
您需要在 OpenClaw/系统 中预装以下基础技能库才能完美运行本流水线：
1. **数据源感知层** (选装其一或全装):
   - `opentwitter-mcp` (来自 infra403，用于稳定抓取推特内容)
   - `opennews-mcp` (来自 infra403，用于稳定抓取新闻源)
2. **加工与发布层** (本套件标配):
   - `redbook-anti-risk-detoxifier-skills` (合规去重与去毒洗稿)
   - `redbook-content-creator-skills` (小红书爆款文案生成结构)
   - `redbook-render-skills` (本地长图文卡片排版生图引擎)

---

## 自动化流水线指令手册 (给 Agent 的执行标准)

当用户下达指令（例：“帮我把 @cryptoxiao 最新的一条推文搬运到小红书”）时，Agent 必须严格、依次在后台执行以下四个阶段的转换，中途不要随意中断或询问，除非遇到报错：

### 🎯 阶段 1：情报猎取 (Information Acquisition)
- 根据用户的指令来源，调用对应的 MCP 工具。
- 如果目标是推特大 V（如 `@cryptoxiao`），请静默调用 `opentwitter-mcp` 获取其最新的推文（Text/Media）。
- 如果目标是海外资讯，请调用 `opennews-mcp` 抓取最新新闻正文。
- **输出**：获得带有高密度干货的 `Raw_Text`（原始文本）。

### 🎯 阶段 2：合规过滤 (Detoxification)
- 将 `Raw_Text` 提交给 `redbook-anti-risk-detoxifier-skills`。
- 严格遵循其禁词表与去毒策略（禁止写翻墙、风控、推特抓取等，转换为云端助手、信息差等国内大白话）。
- **输出**：获得去毒完毕且中性化的 `Safe_Text`。

### 🎯 阶段 3：爆款文案构造 (Content Creation)
- 把 `Safe_Text` 喂给 `redbook-content-creator-skills`。
- 参考其 CES 算法进行强情绪断句编排。
- **输出**：得到结构化的最终文案，包括极具悬念的 `Title`、网感 `Body`、以及高流量标签 `Tags`。

### 🎯 阶段 4：排版与发布 (Rendering & Publishing)
- 定位到 `redbook-render-skills` (或原 `Auto-Redbook-Skills` 目录) 的底层路径。
- 将上一步生成的标题和正文注入，调用其核心 `render_xhs.py` 或 `render_xhs.js` 进行图文卡片的批量出图叠加。
- 最后，执行对应的发布脚本或提示用户审查本地渲染目录中的精美卡片集。

---

## 为什么这么设计？
小白用户或运营者只需**一句话触发此技能**，AI 就会像流水线上的总包工头，自动调度 Twitter 的铲子、去毒的漏斗、写字的笔、排版的画板，在一分钟内给你一套可以直接发往小红书的成品。
