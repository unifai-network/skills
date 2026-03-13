---
name: redbook-content-creator-skills
description: >-
  Generate Xiaohongshu (小红书/RED) content optimized for the platform's CES
  algorithm. Use when creating xiaohongshu posts, writing Chinese social media
  content for RED, generating content with SEO optimization, or planning content
  calendars. Supports diary-style, tutorial, review, and list formats. Must tag
  AI-generated content per 2026 platform rules.
---

# 小红书内容创作 Skill

## 核心算法规则（CES 评分）

- 关注 (8分) > 转发 / 评论 (4分) > 点赞 / 收藏 (1分)
- 初始曝光池 100–500，2 小时内点击率 ≥ 8% + 互动率 ≥ 5% 才进下一级
- **必须标注 `#AI生成内容`**（2026 年 1 月起平台强制要求，否则限流）

---

## 安全规则（先读）

- 每天最多 2 篇，间隔 ≥ 2 小时
- 不发违规内容：医疗建议、金融推荐、政治敏感
- 发布前建议人工审核
- **内容合规必须先通过 `xhs-anti-risk-detoxifier` 检查**（清除高危词汇）

---

## 内容格式要求

| 项目     | 要求                                       |
|----------|--------------------------------------------|
| 标题     | 20 字以内，前 13 字含核心关键词（搜索权重 40%）|
| 正文     | 300–600 字，短句为主，每段 2–3 句           |
| 封面     | 3:4 竖图                                   |
| 标签     | 5–8 个，混合热门 + 长尾                     |

---

## 写作风格模板

### 日记体（推荐，互动率最高）

- 第一人称，有情绪起伏
- 具体细节（时间、数字、场景）
- 结尾留悬念或提问引导评论

### 教程体

- 标题含"教程 / 方法 / 步骤"
- 分步骤，每步配图
- 结尾"关注我获取更多"

### 测评体

- 真实使用体验
- 优缺点对比
- 适合人群推荐

---

## 输出格式

```json
{
  "title": "标题（20字内，前13字含关键词）",
  "content": "正文（300-600字）",
  "tags": ["#标签1", "#标签2", "#AI生成内容"],
  "cover_prompt": "封面图描述（用于AI生成）",
  "best_time": "建议发布时间",
  "cta": "引导互动的结尾语"
}
```

---

## 发布时间建议

| 时段     | 时间                        |
|----------|-----------------------------|
| 早高峰   | 07:00–09:00                 |
| 午休     | 12:00–13:30                 |
| 晚高峰   | 17:30–21:00                 |
| 最佳     | 周二/四/六 19:00–20:00      |
