"""
Tests for collect_session_costs.py — specifically the pricing estimation
fallback when providers don't populate usage.cost.total via OpenRouter.
"""

import json
import os
import tempfile
import textwrap
from unittest import mock

import pytest

# Import the module under test
from collect_session_costs import collect_costs, estimate_cost, fetch_pricing_map


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session_jsonl(messages):
    """Build JSONL content from a list of (model, usage_dict) tuples."""
    lines = []
    for model, usage in messages:
        entry = {
            "type": "message",
            "timestamp": "2026-03-22T10:00:00Z",
            "message": {
                "role": "assistant",
                "model": model,
                "usage": usage,
            },
        }
        lines.append(json.dumps(entry))
    return "\n".join(lines) + "\n"


def _setup_session_dir(tmp_path, sessions):
    """
    Create a fake ~/.openclaw/agents/default/sessions/ dir with JSONL files.
    sessions: dict of {session_id: jsonl_content}
    """
    session_dir = os.path.join(tmp_path, ".openclaw", "agents", "default", "sessions")
    os.makedirs(session_dir, exist_ok=True)
    for sid, content in sessions.items():
        with open(os.path.join(session_dir, f"{sid}.jsonl"), "w") as f:
            f.write(content)
    return session_dir


# ---------------------------------------------------------------------------
# estimate_cost (pure function)
# ---------------------------------------------------------------------------

class TestEstimateCost:
    PRICING_MAP = {
        "minimax/minimax-m2.7": {
            "prompt": 0.0000003,
            "completion": 0.0000012,
            "cache_read": 0.00000006,
        },
        "nvidia/nemotron-3-super-120b-a12b": {
            "prompt": 0.0000001,
            "completion": 0.0000005,
            "cache_read": 0.00000004,
        },
        "stepfun/step-3.5-flash": {
            "prompt": 0.0000001,
            "completion": 0.0000003,
            "cache_read": 0.00000002,
        },
    }

    def test_minimax_cost_estimation(self):
        # 26300 uncached * $0.30/M + 297700 cached * $0.06/M + 8200 out * $1.20/M
        cost, found = estimate_cost(
            "minimax/minimax-m2.7", 26300, 297700, 8200, self.PRICING_MAP
        )
        assert found is True
        assert round(cost, 4) == round(0.00789 + 0.017862 + 0.00984, 4)
        assert cost > 0.03  # ~$0.036

    def test_nemotron_cost_estimation(self):
        # 1.4M uncached + 2.3K cached + 37.2K out
        cost, found = estimate_cost(
            "nvidia/nemotron-3-super-120b-a12b", 1400000, 2300, 37200, self.PRICING_MAP
        )
        assert found is True
        assert cost > 0.15  # ~$0.159

    def test_unknown_model_returns_zero(self):
        cost, found = estimate_cost(
            "unknown/model", 100000, 50000, 10000, self.PRICING_MAP
        )
        assert found is False
        assert cost == 0.0

    def test_zero_tokens(self):
        cost, found = estimate_cost(
            "minimax/minimax-m2.7", 0, 0, 0, self.PRICING_MAP
        )
        assert found is True
        assert cost == 0.0

    def test_empty_pricing_map(self):
        cost, found = estimate_cost(
            "minimax/minimax-m2.7", 100000, 0, 10000, {}
        )
        assert found is False
        assert cost == 0.0

    def test_openrouter_prefix_stripped(self):
        """Session JSONL may store model as openrouter/provider/model; pricing map uses provider/model."""
        cost, found = estimate_cost(
            "openrouter/minimax/minimax-m2.7", 26300, 297700, 8200, self.PRICING_MAP
        )
        assert found is True
        assert cost > 0.03  # same as test_minimax_cost_estimation

    def test_openrouter_prefix_not_stripped_when_unnecessary(self):
        """Exact match takes priority over prefix stripping."""
        special_pricing = {
            **self.PRICING_MAP,
            "openrouter/minimax/minimax-m2.7": {
                "prompt": 0.001,
                "completion": 0.002,
                "cache_read": 0.0005,
            },
        }
        cost, found = estimate_cost(
            "openrouter/minimax/minimax-m2.7", 1000, 0, 1000, special_pricing
        )
        assert found is True
        # Should use the exact match (0.001*1000 + 0.002*1000 = 3.0), not the stripped one
        assert round(cost, 4) == 3.0


# ---------------------------------------------------------------------------
# collect_costs — integration with session files
# ---------------------------------------------------------------------------

class TestCollectCostsIntegration:
    """Test the full collect_costs flow with mocked session files and pricing API."""

    def test_session_with_real_cost_uses_reported_value(self, tmp_path):
        """When usage.cost.total > 0, use the reported cost (no estimation)."""
        content = _make_session_jsonl([
            ("anthropic/claude-sonnet-4", {
                "input": 10000, "output": 2000, "cacheRead": 5000,
                "cost": {"input": 0.03, "output": 0.03, "cacheRead": 0.004, "total": 0.064},
            }),
        ])
        _setup_session_dir(str(tmp_path), {"sess-real": content})

        with mock.patch("os.path.expanduser", return_value=str(tmp_path)):
            # Should NOT call fetch_pricing_map since cost is reported
            with mock.patch("collect_session_costs.fetch_pricing_map") as mock_fetch:
                import io, sys
                captured = io.StringIO()
                sys.stdout = captured
                collect_costs()
                sys.stdout = sys.__stdout__

                results = json.loads(captured.getvalue())
                assert len(results) == 1
                assert results[0]["costUsd"] == 0.064
                assert results[0]["costEstimated"] is False
                mock_fetch.assert_not_called()

    def test_session_with_zero_cost_triggers_estimation(self, tmp_path):
        """When usage.cost.total == 0 but tokens present, estimate from pricing."""
        content = _make_session_jsonl([
            ("minimax/minimax-m2.7", {
                "input": 26300, "output": 8200, "cacheRead": 297700,
                "cost": {"total": 0},
            }),
        ])
        _setup_session_dir(str(tmp_path), {"sess-zero": content})

        fake_pricing = {
            "minimax/minimax-m2.7": {
                "prompt": 0.0000003,
                "completion": 0.0000012,
                "cache_read": 0.00000006,
            },
        }

        with mock.patch("os.path.expanduser", return_value=str(tmp_path)):
            with mock.patch(
                "collect_session_costs.fetch_pricing_map", return_value=fake_pricing
            ):
                import io, sys
                captured = io.StringIO()
                sys.stdout = captured
                collect_costs()
                sys.stdout = sys.__stdout__

                results = json.loads(captured.getvalue())
                assert len(results) == 1
                assert results[0]["costEstimated"] is True
                assert results[0]["costUsd"] > 0.03  # ~$0.036

    def test_mixed_sessions_only_estimate_zero_cost(self, tmp_path):
        """Real-cost sessions untouched; zero-cost sessions get estimated."""
        real_cost = _make_session_jsonl([
            ("anthropic/claude-opus-4.6", {
                "input": 800000, "output": 26000, "cacheRead": 4000000,
                "cost": {"total": 6.70},
            }),
        ])
        zero_cost = _make_session_jsonl([
            ("minimax/minimax-m2.7", {
                "input": 26300, "output": 8200, "cacheRead": 297700,
                "cost": {"total": 0},
            }),
        ])
        _setup_session_dir(str(tmp_path), {
            "sess-judge": real_cost,
            "sess-model": zero_cost,
        })

        fake_pricing = {
            "minimax/minimax-m2.7": {
                "prompt": 0.0000003,
                "completion": 0.0000012,
                "cache_read": 0.00000006,
            },
        }

        with mock.patch("os.path.expanduser", return_value=str(tmp_path)):
            with mock.patch(
                "collect_session_costs.fetch_pricing_map", return_value=fake_pricing
            ):
                import io, sys
                captured = io.StringIO()
                sys.stdout = captured
                collect_costs()
                sys.stdout = sys.__stdout__

                results = json.loads(captured.getvalue())
                assert len(results) == 2

                by_model = {r["model"]: r for r in results}
                judge = by_model["anthropic/claude-opus-4.6"]
                model = by_model["minimax/minimax-m2.7"]

                assert judge["costUsd"] == 6.7
                assert judge["costEstimated"] is False
                assert model["costEstimated"] is True
                assert model["costUsd"] > 0

    def test_openrouter_prefixed_model_gets_estimated(self, tmp_path):
        """Session JSONL model field has openrouter/ prefix; pricing map uses bare ID."""
        content = _make_session_jsonl([
            ("openrouter/z-ai/glm-5-turbo", {
                "input": 27950, "output": 9464, "cacheRead": 490211,
                "cost": {"total": 0},
            }),
        ])
        _setup_session_dir(str(tmp_path), {"sess-prefixed": content})

        fake_pricing = {
            "z-ai/glm-5-turbo": {
                "prompt": 0.0000005,
                "completion": 0.000002,
                "cache_read": 0.00000025,
            },
        }

        with mock.patch("os.path.expanduser", return_value=str(tmp_path)):
            with mock.patch(
                "collect_session_costs.fetch_pricing_map", return_value=fake_pricing
            ):
                import io, sys
                captured = io.StringIO()
                sys.stdout = captured
                collect_costs()
                sys.stdout = sys.__stdout__

                results = json.loads(captured.getvalue())
                assert len(results) == 1
                assert results[0]["costEstimated"] is True
                assert results[0]["costUsd"] > 0
                assert results[0]["model"] == "openrouter/z-ai/glm-5-turbo"

    def test_zero_cost_with_failed_pricing_fetch(self, tmp_path):
        """When pricing fetch fails, zero-cost sessions stay at 0."""
        content = _make_session_jsonl([
            ("minimax/minimax-m2.7", {
                "input": 26300, "output": 8200, "cacheRead": 297700,
                "cost": {"total": 0},
            }),
        ])
        _setup_session_dir(str(tmp_path), {"sess-fail": content})

        with mock.patch("os.path.expanduser", return_value=str(tmp_path)):
            with mock.patch(
                "collect_session_costs.fetch_pricing_map", return_value={}
            ):
                import io, sys
                captured = io.StringIO()
                sys.stdout = captured
                collect_costs()
                sys.stdout = sys.__stdout__

                results = json.loads(captured.getvalue())
                assert len(results) == 1
                assert results[0]["costUsd"] == 0
                assert results[0]["costEstimated"] is False


# ---------------------------------------------------------------------------
# fetch_pricing_map (network call — test with mock)
# ---------------------------------------------------------------------------

class TestFetchPricingMap:
    MOCK_OPENROUTER_RESPONSE = json.dumps({
        "data": [
            {
                "id": "minimax/minimax-m2.7",
                "name": "MiniMax M2.7",
                "pricing": {
                    "prompt": "0.0000003",
                    "completion": "0.0000012",
                    "prompt_cache_read": "0.00000006",
                },
            },
            {
                "id": "free/model",
                "name": "Free Model",
                "pricing": {"prompt": "0", "completion": "0"},
            },
        ]
    }).encode()

    def test_parses_openrouter_response(self):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = self.MOCK_OPENROUTER_RESPONSE
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            pricing = fetch_pricing_map()

        assert "minimax/minimax-m2.7" in pricing
        p = pricing["minimax/minimax-m2.7"]
        assert p["prompt"] == 0.0000003
        assert p["completion"] == 0.0000012
        assert p["cache_read"] == 0.00000006

    def test_skips_models_without_pricing(self):
        resp_data = json.dumps({
            "data": [
                {"id": "no-pricing/model", "name": "No Pricing"},
                {
                    "id": "has-pricing/model",
                    "name": "Has Pricing",
                    "pricing": {"prompt": "0.001", "completion": "0.002"},
                },
            ]
        }).encode()
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = resp_data
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            pricing = fetch_pricing_map()

        assert "no-pricing/model" not in pricing
        assert "has-pricing/model" in pricing

    def test_returns_empty_on_network_error(self):
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("network error")
        ):
            pricing = fetch_pricing_map()
            assert pricing == {}

    def test_cache_read_falls_back_to_prompt_price(self):
        resp_data = json.dumps({
            "data": [
                {
                    "id": "no-cache/model",
                    "name": "No Cache Pricing",
                    "pricing": {"prompt": "0.001", "completion": "0.002"},
                },
            ]
        }).encode()
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = resp_data
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            pricing = fetch_pricing_map()

        p = pricing["no-cache/model"]
        assert p["cache_read"] == p["prompt"]  # fallback to prompt price
