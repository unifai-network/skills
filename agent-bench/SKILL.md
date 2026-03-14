---
name: agent-bench
description: "Benchmark and compare the agentic performance of multiple LLM models on the same task. Use this skill when the user wants to compare models, benchmark LLMs, test which model is better at a task, race models against each other, or evaluate model performance side-by-side. Triggers on phrases like 'benchmark models', 'compare opus vs sonnet', 'which model is better at', 'race these models', 'test model performance', 'agent benchmark'."
---

# Agent Bench — Multi-Model Agentic Benchmark

You are the **judge agent**. Your job is to give the same task to multiple models running as subagents in parallel, then evaluate and compare their outputs fairly.

## Inputs

The user provides:
- **Task**: A description of the work each agent should perform
- **Models**: Which models to benchmark (e.g., "opus, sonnet, haiku")
- **Timeout** (optional): Max time per agent. Default: 10 minutes

## Workflow

### 1. Parse and Confirm

Extract the task, model list, and timeout from the user's message. Before proceeding, briefly confirm:
- The exact task each subagent will receive
- The models being benchmarked
- The timeout value

Wait for the user to confirm or adjust.

### 2. Prepare Isolated Workspaces

Each subagent needs its own directory so their files don't collide. This is critical — without isolation, subagents running in parallel will overwrite each other's output files.

Create a timestamped benchmark directory with one subdirectory per model:
```
.agent-bench/<YYYYMMDD-HHmmss>/
├── opus/
├── sonnet/
├── haiku/
└── results.json
```

Create these directories before spawning any subagents. Add `.agent-bench/` to `.gitignore` if the project uses git.

### 3. Spawn Subagents

Launch one subagent per model, all in the same turn (parallel). Each subagent receives an identical prompt — just the task, as if it came directly from a user. Do not mention benchmarking, scoring, or evaluation. The subagent should behave exactly as it would for a real user request.

Prompt template:

```
<task, verbatim from the user>

Use <absolute-path-to-model-directory> as your working directory for any files you create or modify.
```

Each subagent gets its own unique directory path (e.g., `.agent-bench/20260314-100000/opus/`). Keep the prompt natural — the workspace instruction is a reasonable constraint that wouldn't seem unusual to any agent.

If the runtime also supports additional isolation mechanisms (e.g., `isolation: "worktree"` in Claude Code), use them as an extra layer of protection. But always assign per-model directories regardless — this is the universal, runtime-agnostic safeguard.

Other implementation details:
- Each subagent must start with a clean context (no shared history)
- If the runtime supports model selection for subagents, use it to assign the correct model
- If the runtime supports background/async execution, use it so all models run in parallel
- If the runtime supports timeout for subagents, apply the configured timeout

### 4. Collect Results

As each subagent completes (or times out), record:
- **Duration**: Wall-clock time from spawn to completion (seconds)
- **Tokens**: Total token usage if available from the runtime (otherwise mark as "N/A")
- **Tool uses**: Number of tool calls if available (otherwise mark as "N/A")
- **Status**: "completed", "timed_out", or "error"
- **Response**: The subagent's final response text
- **Workspace path**: Where the model's files live

If a subagent times out, record what it managed to produce (partial results still get evaluated).

### 5. Evaluate Each Model

Now act as an impartial judge. For each model:

1. Read the subagent's response text
2. List and read the files in the model's workspace directory
3. If the task involved code, attempt to run/test it (within the model's workspace)
4. If the task involved writing, research, or analysis, evaluate the substance and presentation
5. Score on three dimensions:

| Metric | Scale | What it measures |
|--------|-------|------------------|
| **Completeness** | 0–10 | Did the agent address all parts of the task? 10 = every requirement met, 0 = nothing done |
| **Quality** | 0–10 | How good is the output? Accuracy, depth, clarity, structure, attention to detail. Adapt criteria to the task type — code quality for coding tasks, writing quality for writing tasks, analytical rigor for research tasks, etc. |
| **Overall** | 0–10 | Holistic score weighing both completeness and quality, plus any other impressions (creativity, efficiency, going above and beyond) |

For each score, write a 1-2 sentence justification. Be specific — reference actual outputs, files, or content.

Evaluation integrity matters: evaluate each model's output independently. Read and score one model fully before moving to the next, so earlier scores don't anchor later ones. If you catch yourself comparing during scoring, reset and evaluate against the task requirements only.

### 6. Present Results

Output a **summary table** in markdown:

```
## Benchmark Results

**Task**: <brief task description>
**Timeout**: <value>
**Date**: <timestamp>

| Model | Completeness | Quality | Overall | Duration | Tokens | Status |
|-------|-------------|---------|---------|----------|--------|--------|
| opus  | 9           | 8       | 9       | 45s      | 12,340 | completed |
| sonnet| 8           | 9       | 8       | 32s      | 8,210  | completed |
| haiku | 6           | 5       | 5       | 18s      | 4,100  | completed |
```

Then for each model, show:
- Score justifications (the 1-2 sentences per metric)
- Notable strengths or weaknesses
- Key outputs produced (with file paths if applicable)

End with a brief **verdict**: which model performed best for this task and why, noting any interesting tradeoffs (e.g., "sonnet was faster and cheaper but opus produced more thorough analysis").

### 7. Save Results

Write structured results to `results.json` in a `.agent-bench/<YYYYMMDD-HHmmss>/` directory within the current working directory (add `.agent-bench/` to `.gitignore` if the project uses git):

```json
{
  "task": "the task description",
  "timeout_seconds": 600,
  "timestamp": "2025-01-15T10:30:00Z",
  "models": [
    {
      "model": "opus",
      "status": "completed",
      "duration_seconds": 45,
      "total_tokens": 12340,
      "tool_uses": 15,
      "scores": {
        "completeness": 9,
        "quality": 8,
        "overall": 9
      },
      "justifications": {
        "completeness": "...",
        "quality": "...",
        "overall": "..."
      },
      "workspace": "<path to model's workspace>"
    }
  ],
  "verdict": "..."
}
```

Tell the user where the benchmark directory and each model's workspace are so they can inspect individual outputs.

## Tips for Good Benchmark Tasks

When the user's task is vague, you can suggest they make it more specific. Good benchmark tasks have clear success criteria so scoring is less subjective.

Examples across different categories:

- **Coding**: "Write a Python CLI that converts CSV to JSON, handling quoted commas and multiline fields. Include tests."
- **Research**: "Find the top 5 trending AI papers this week, summarize each in 2-3 sentences, and explain why they matter."
- **Writing**: "Write a professional email declining a vendor proposal while keeping the relationship warm for future opportunities."
- **Analysis**: "Here's a sales CSV [attach file]. Identify the top 3 trends and create a summary report with key insights."
- **Productivity**: "Create a weekly meal plan for a family of 4 with a $150 budget, including a shopping list organized by store section."
- **Multi-step**: "Research the current weather in Tokyo, write a short travel advisory, and save it as a formatted markdown file."
