#!/usr/bin/env python3
"""
Collect per-session USD costs from OpenClaw session JSONL files.

Reads all session JSONL files on the agent, sums usage and cost fields from
assistant messages, and outputs JSON with per-session cost data.

When a provider doesn't populate usage.cost.total (returns 0), fetches model
pricing from OpenRouter and estimates cost from token counts.

Usage:
    python3 scripts/collect_session_costs.py

Output (JSON array to stdout):
    [
      {
        "sessionId": "abc123",
        "model": "anthropic/claude-sonnet-4",
        "provider": "openrouter",
        "costUsd": 0.0523,
        "costEstimated": false,
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
import sys
import urllib.request


def fetch_pricing_map():
    """Fetch model pricing from OpenRouter API. Returns {model_id: {prompt, completion, cache_read}} per-token USD."""
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"User-Agent": "openclaw-bench/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        pricing = {}
        for m in data.get("data", []):
            p = m.get("pricing", {})
            prompt = p.get("prompt")
            completion = p.get("completion")
            if prompt and completion:
                prompt_f = float(prompt)
                completion_f = float(completion)
                cache_read_raw = p.get("prompt_cache_read")
                cache_read_f = float(cache_read_raw) if cache_read_raw else prompt_f
                pricing[m["id"]] = {
                    "prompt": prompt_f,
                    "completion": completion_f,
                    "cache_read": cache_read_f,
                }
        return pricing
    except Exception as e:
        print(f"Warning: failed to fetch OpenRouter pricing: {e}", file=sys.stderr)
        return {}


def estimate_cost(model, tokens_input, tokens_cache_read, tokens_output, pricing_map):
    """Estimate USD cost from token counts and OpenRouter pricing. Returns (cost_usd, found)."""
    pricing = pricing_map.get(model)
    if not pricing:
        return 0.0, False
    cost = (
        tokens_input * pricing["prompt"]
        + tokens_cache_read * pricing["cache_read"]
        + tokens_output * pricing["completion"]
    )
    return cost, True


def collect_costs():
    home = os.path.expanduser("~")

    # Search all known session directory patterns
    session_dirs = glob.glob(os.path.join(home, ".openclaw/agents/*/sessions"))
    session_dirs.extend(glob.glob(os.path.join(home, ".openclaw/sessions")))

    all_files = []
    for d in session_dirs:
        all_files.extend(glob.glob(os.path.join(d, "*.jsonl")))

    results = []
    # Track which sessions need pricing estimation
    needs_estimation = []

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
            entry = {
                "sessionId": session_id,
                "model": model,
                "provider": provider,
                "costUsd": round(cost_total, 6),
                "costEstimated": False,
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
            results.append(entry)
            # If cost is zero but tokens are present, needs estimation
            if cost_total == 0 and (tokens_input > 0 or tokens_output > 0):
                needs_estimation.append(entry)

    # Fetch pricing and estimate costs for sessions with zero cost
    if needs_estimation:
        pricing_map = fetch_pricing_map()
        if pricing_map:
            for entry in needs_estimation:
                estimated, found = estimate_cost(
                    entry["model"],
                    entry["tokens"]["input"],
                    entry["tokens"]["cacheRead"],
                    entry["tokens"]["output"],
                    pricing_map,
                )
                if found and estimated > 0:
                    entry["costUsd"] = round(estimated, 6)
                    entry["costEstimated"] = True
                    entry["cost"]["total"] = round(estimated, 6)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    collect_costs()
