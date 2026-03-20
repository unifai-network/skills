#!/usr/bin/env python3
"""
Collect per-session USD costs from OpenClaw session JSONL files.

Reads all session JSONL files on the agent, sums usage and cost fields from
assistant messages, and outputs JSON with per-session cost data.

Usage:
    python3 scripts/collect_session_costs.py

Output (JSON array to stdout):
    [
      {
        "sessionId": "abc123",
        "model": "anthropic/claude-sonnet-4",
        "provider": "openrouter",
        "costUsd": 0.0523,
        "cost": {
          "input": 0.04,
          "output": 0.01,
          "cacheRead": 0.002,
          "cacheWrite": 0.0003,
          "total": 0.0523
        },
        "tokens": {
          "input": 12000,
          "output": 3500,
          "cacheRead": 8000,
          "cacheWrite": 500,
          "total": 24000
        }
      },
      ...
    ]
"""

import json
import os
import glob


def collect_costs():
    home = os.path.expanduser("~")

    # Search all known session directory patterns
    session_dirs = glob.glob(os.path.join(home, ".openclaw/agents/*/sessions"))
    session_dirs.extend(glob.glob(os.path.join(home, ".openclaw/sessions")))

    all_files = []
    for d in session_dirs:
        all_files.extend(glob.glob(os.path.join(d, "*.jsonl")))

    results = []
    for f in all_files:
        session_id = os.path.basename(f).replace(".jsonl", "")
        model = None
        provider = None
        cost_input = 0.0
        cost_output = 0.0
        cost_cache_read = 0.0
        cost_cache_write = 0.0
        cost_total = 0.0
        tokens_input = 0
        tokens_output = 0
        tokens_cache_read = 0
        tokens_cache_write = 0
        tokens_total = 0

        with open(f) as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get("message", {})
                if obj.get("type") == "message" and msg.get("role") == "assistant":
                    if msg.get("model"):
                        model = msg["model"]
                    if msg.get("provider"):
                        provider = msg["provider"]
                    usage = msg.get("usage", {})
                    cost = usage.get("cost", {})
                    cost_input += cost.get("input", 0)
                    cost_output += cost.get("output", 0)
                    cost_cache_read += cost.get("cacheRead", 0)
                    cost_cache_write += cost.get("cacheWrite", 0)
                    cost_total += cost.get("total", 0)
                    tokens_input += usage.get("input", 0)
                    tokens_output += usage.get("output", 0)
                    tokens_cache_read += usage.get("cacheRead", 0)
                    tokens_cache_write += usage.get("cacheWrite", 0)
                    tokens_total += usage.get("totalTokens", 0)

        if model:
            results.append(
                {
                    "sessionId": session_id,
                    "model": model,
                    "provider": provider,
                    "costUsd": round(cost_total, 6),
                    "cost": {
                        "input": round(cost_input, 6),
                        "output": round(cost_output, 6),
                        "cacheRead": round(cost_cache_read, 6),
                        "cacheWrite": round(cost_cache_write, 6),
                        "total": round(cost_total, 6),
                    },
                    "tokens": {
                        "input": tokens_input,
                        "output": tokens_output,
                        "cacheRead": tokens_cache_read,
                        "cacheWrite": tokens_cache_write,
                        "total": tokens_total,
                    },
                }
            )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    collect_costs()
