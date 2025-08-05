#!/usr/bin/env python3
"""
Coinalyze-powered Solana Derivatives Agent
-----------------------------------------
Fetches key derivative metrics for SOL from the public Coinalyze API and asks
the `o3` model for a concise directional view suitable for WhatsApp delivery.

Metrics used
============
• Open Interest (OI)
• Funding Rate (FR)
• Liquidations (LQ) – last 1 h long & short volume
• Global Long/Short Ratio (LS)
• Basis (difference between perp and spot price) – last close

Environment
===========
COINALYZE_API_KEY  – your free key from https://coinalyze.net
OPENAI_API_KEY     – key for OpenAI (o3 / gpt-4 fallback)

Usage
=====
$ python coinalyze_solana_agent.py                # prints analysis
$ python coinalyze_solana_agent.py --whatsapp     # sends to WhatsApp via Twilio

(WhatsApp requires the same env vars as whatsapp_sender.py)
"""
from __future__ import annotations

import os
import time
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple
import requests
from dotenv import load_dotenv

# 3rd-party optional – only import when needed
try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

load_dotenv()

API_BASE = "https://api.coinalyze.net/v1"

################################################################################
# Utility helpers
################################################################################

def _ts_now() -> int:
    return int(time.time())


def _ts_minus(seconds: int) -> int:
    return _ts_now() - seconds


def _get(url: str, params: Dict[str, Any] | None = None) -> Any:
    """Thin wrapper around GET with API key handling & clearer errors.

    Raises
    ------
    RuntimeError
        If the `COINALYZE_API_KEY` environment variable is missing.
    requests.HTTPError
        Propagated if the response status is not 2xx. Adds hint when 401.
    """
    params = params.copy() if params else {}

    api_key = os.getenv("COINALYZE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COINALYZE_API_KEY environment variable not set – sign up at https://coinalyze.net to obtain a free key "
            "and export it before running."
        )

    # The API accepts the key via header or query param. Use header to avoid exposing it in logs.
    headers = {"api_key": api_key}

    resp = requests.get(f"{API_BASE}{url}", params=params, headers=headers, timeout=15)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        if resp.status_code == 401:
            raise RuntimeError("Unauthorized (401) – check that your COINALYZE_API_KEY is correct & still active") from exc
        raise
    return resp.json()

################################################################################
# Data agent
################################################################################

class CoinalyzeDataAgent:
    """Fetch SOL derivative metrics from Coinalyze."""

    def __init__(self, perp_symbol: str = "SOLUSDT_PERP.A", spot_symbol: str = "SOLUSDT.C"):
        # TODO: make dynamic lookup via /future-markets & /spot-markets if needed
        self.perp_symbol = perp_symbol
        self.spot_symbol = spot_symbol

    # ---------------------------------------------------------------------
    # Current values
    # ---------------------------------------------------------------------
    def current_open_interest(self) -> float:
        data = _get("/open-interest", {"symbols": self.perp_symbol, "convert_to_usd": "true"})
        return float(data[0]["value"])

    def current_funding_rate(self) -> float:
        data = _get("/funding-rate", {"symbols": self.perp_symbol})
        return float(data[0]["value"])

    # ---------------------------------------------------------------------
    # Recent history (last 1 hour)
    # ---------------------------------------------------------------------
    def liquidation_last_hour(self) -> Tuple[float, float]:
        to_ts = _ts_now()
        from_ts = _ts_minus(3600)
        data = _get(
            "/liquidation-history",
            {
                "symbols": self.perp_symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts,
                "convert_to_usd": "true",
            },
        )
        history = data[0]["history"] if data else []
        long_vol = sum(item.get("l", 0) for item in history)  # long liquidations volume
        short_vol = sum(item.get("s", 0) for item in history)  # short liquidations volume
        return long_vol, short_vol

    def ls_ratio_last_hour(self) -> float:
        to_ts = _ts_now()
        from_ts = _ts_minus(3600)
        data = _get(
            "/long-short-ratio-history",
            {
                "symbols": self.perp_symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts,
            },
        )
        history = data[0]["history"] if data else []
        if not history:
            return float("nan")
        # Take the latest point
        latest = history[-1]
        return float(latest.get("r", 0))

    # ---------------------------------------------------------------------
    # Basis calculation
    # ---------------------------------------------------------------------
    def basis(self) -> float:
        """Return basis % = (perp_price - spot_price) / spot_price * 100."""
        to_ts = _ts_now()
        from_ts = _ts_minus(300)  # last 5 min
        params = {
            "interval": "1min",
            "from": from_ts,
            "to": to_ts,
        }
        perp_data = _get("/ohlcv-history", {**params, "symbols": self.perp_symbol})
        spot_data = _get("/ohlcv-history", {**params, "symbols": self.spot_symbol})
        if not perp_data or not spot_data:
            return float("nan")
        perp_close = perp_data[0]["history"][-1]["c"]
        spot_close = spot_data[0]["history"][-1]["c"]
        return (perp_close - spot_close) / spot_close * 100

    # ---------------------------------------------------------------------
    # Aggregate fetch
    # ---------------------------------------------------------------------
    def fetch_all(self) -> Dict[str, Any]:
        long_lq, short_lq = self.liquidation_last_hour()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_interest_usd": self.current_open_interest(),
            "funding_rate": self.current_funding_rate(),
            "liquidations_long_usd_1h": long_lq,
            "liquidations_short_usd_1h": short_lq,
            "long_short_ratio_1h": self.ls_ratio_last_hour(),
            "basis_pct": self.basis(),
        }

################################################################################
# Correlation analysis helpers
################################################################################

import numpy as np


def fetch_24h_series(agent: "CoinalyzeDataAgent") -> Dict[str, list[float]]:
    """Fetch 24×1-hour series for key metrics via Coinalyze."""
    to_ts = _ts_now()
    from_ts = _ts_minus(86400)
    base_params = {"interval": "1hour", "from": from_ts, "to": to_ts}

    # ---------------- Current endpoints ----------------
    oi_hist = _get(
        "/open-interest-history",
        {
            **base_params,
            "symbols": agent.perp_symbol,
            "convert_to_usd": "true",
        },
    )[0]["history"]
    # Prefer close price 'c'; fall back to 'v' or 'value' for backward compatibility
    oi_series = [float(x.get("c") or x.get("v") or x.get("value", 0)) for x in oi_hist][-24:]

    fr_hist = _get(
        "/funding-rate-history",
        {**base_params, "symbols": agent.perp_symbol},
    )[0]["history"]
    # Funding rate history returns OHLC; use close 'c' when present
    fr_series = [float(x.get("c") or x.get("v") or x.get("value", 0)) for x in fr_hist][-24:]

    lq_hist = _get(
        "/liquidation-history",
        {**base_params, "symbols": agent.perp_symbol, "convert_to_usd": "true"},
    )[0]["history"]
    long_liq_series = [float(x.get("l", 0)) for x in lq_hist][-24:]
    short_liq_series = [float(x.get("s", 0)) for x in lq_hist][-24:]

    ls_hist = _get(
        "/long-short-ratio-history",
        {**base_params, "symbols": agent.perp_symbol},
    )[0]["history"]
    ls_series = [float(x.get("r", 0)) for x in ls_hist][-24:]

    # Basis via OHLCV – compute hourly close diff
    perp_hist = _get(
        "/ohlcv-history",
        {**base_params, "symbols": agent.perp_symbol},
    )[0]["history"]
    spot_hist = _get(
        "/ohlcv-history",
        {**base_params, "symbols": agent.spot_symbol},
    )[0]["history"]
    basis_series = [
        ((p["c"] - s["c"]) / s["c"] * 100) if s["c"] else 0 for p, s in zip(perp_hist[-24:], spot_hist[-24:])
    ]

    return {
        "open_interest_usd": oi_series,
        "funding_rate": fr_series,
        "liq_long_usd": long_liq_series,
        "liq_short_usd": short_liq_series,
        "ls_ratio": ls_series,
        "basis_pct": basis_series,
    }


def correlation_matrix(series: Dict[str, list[float]]) -> Dict[tuple[str, str], float]:
    """Return Pearson r for every metric pair (upper triangle)."""
    keys = list(series.keys())
    arr = np.array([series[k] for k in keys])
    corr = np.corrcoef(arr)
    result: Dict[tuple[str, str], float] = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            result[(keys[i], keys[j])] = float(corr[i, j])
    return result

################################################################################
# AI analysis
################################################################################

def ai_direction(metrics: Dict[str, Any]) -> str:
    """Ask o3 / GPT-4 for a one-liner trading direction."""
    if OpenAI is None:
        raise ImportError("openai not installed – run `uv add openai`")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "Provide a concise (max 2 sentences) directional view for SOL/USDT futures "
        "based solely on the following derivative metrics. Respond with LONG, SHORT, NEUTRAL or UNCLEAR (if data is inconclusive) plus one brief justification.\n\n"
        f"Open Interest: {metrics['open_interest_usd']:.0f} USD\n"
        f"Funding Rate: {metrics['funding_rate']*100:.4f}%\n"
        f"Liquidations 1h – Long: {metrics['liquidations_long_usd_1h']:.0f} USD, Short: {metrics['liquidations_short_usd_1h']:.0f} USD\n"
        f"Long/Short Ratio 1h: {metrics['long_short_ratio_1h']:.2f}\n"
        f"Basis: {metrics['basis_pct']:.2f}%"
    )

    try:
        print("🧠 Engaging o3 model for directional analysis...")
        resp = client.chat.completions.create(
            model="o3",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an elite cryptocurrency derivatives trader specializing in pattern recognition and market sentiment analysis. Focus on identifying subtle shifts in positioning, funding dynamics, and liquidation risks that indicate directional opportunities."
                },
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=200,  # More tokens for better o3 insights
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"⚠️ o3 model error: {exc}")
        # fallback to GPT-4
        try:
            print("🔄 Falling back to GPT-4...")
            resp = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as fallback_e:
            return f"Analysis unavailable. o3 error: {exc}, GPT-4 error: {fallback_e}"

################################################################################
# Correlation AI summary
################################################################################

def ai_correlation_summary(corr: Dict[tuple[str, str], float]) -> str:
    """Ask o3 to highlight key correlations and risks in ≤4 lines."""
    if OpenAI is None:
        raise ImportError("openai not installed – run `uv add openai`")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build compact data string like "metric1/metric2:0.85, metricA/metricB:-0.63, …"
    data_str = ", ".join([
        f"{a}/{b}:{v:.2f}" for (a, b), v in corr.items()
    ])

    prompt = (
        "Given the following Pearson correlations (last 24×1-hour points) for SOL derivative metrics, "
        "write at most 4 short lines that flag notable relationships, possible price reversions or risks. "
        "Keep it concise and trader-friendly.\n\n" + data_str
    )

    try:
        print("🧠 Engaging o3 model for correlation analysis...")
        resp = client.chat.completions.create(
            model="o3",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert quantitative analyst specializing in derivatives market correlations and risk assessment. Focus on identifying key relationships that indicate potential price reversions, cascade risks, or positioning imbalances."
                },
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=180,  # More tokens for detailed correlation insights
        )
        return "\n".join(resp.choices[0].message.content.strip().splitlines())  # preserve lines
    except Exception as e:
        print(f"⚠️ o3 correlation analysis error: {e}")
        return f"Correlation analysis unavailable: {e}"

################################################################################
# WhatsApp helper wrapper
################################################################################

def whatsapp_summary(metrics: Dict[str, Any], direction: str, corr_lines: str | None = None) -> str:
    """Return ≤10 lines suitable for WhatsApp (snapshot + optional correlation lines)."""
    clean_dir = " ".join(direction.splitlines()).strip()
    parts = [
        "📊 SOL Deriv Snapshot",
        f"OI ${metrics['open_interest_usd'] / 1e6:.1f}M | FR {metrics['funding_rate']*100:.4f}%",
        (
            f"Liq1h L/S ${metrics['liquidations_long_usd_1h'] / 1e6:.2f}M/"
            f"${metrics['liquidations_short_usd_1h'] / 1e6:.2f}M | LS {metrics['long_short_ratio_1h']:.2f}"
        ),
        f"Basis {metrics['basis_pct']:.2f}%",
    ]
    if corr_lines:
        parts.extend(corr_lines.split("\n")[:4])  # ensure ≤4 lines
    parts.append(f"➡️ {clean_dir}")
    return "\n".join(parts)

################################################################################
# CLI entry point
################################################################################


def main() -> None:
    parser = argparse.ArgumentParser(description="SOL derivative metrics via Coinalyze")
    parser.add_argument("--whatsapp", action="store_true", help="Send summary via WhatsApp")
    args = parser.parse_args()

    agent = CoinalyzeDataAgent()
    print("🔍 Fetching metrics from Coinalyze …")
    metrics = agent.fetch_all()
    print(json.dumps(metrics, indent=2))

    # 24h correlation analysis
    series_24h = fetch_24h_series(agent)
    corr = correlation_matrix(series_24h)
    corr_summary = ai_correlation_summary(corr)

    direction = ai_direction(metrics)
    summary = whatsapp_summary(metrics, direction, corr_summary)

    print("\n====== WHATSAPP SUMMARY ======")
    print(summary)

    if args.whatsapp:
        try:
            from whatsapp_sender import WhatsAppSender  # local module
        except ImportError as exc:  # pragma: no cover
            print("❌ whatsapp_sender module not found:", exc)
            return
        sender = WhatsAppSender()
        sender.send_message(summary)


if __name__ == "__main__":
    main()
