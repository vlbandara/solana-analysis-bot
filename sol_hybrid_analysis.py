#!/usr/bin/env python3
"""
SOL Hybrid Analysis - Best of Both Worlds
=========================================
Combines Coinalyze's precise derivatives data with Sonar's enhanced technical analysis
and real-time news capabilities for optimal SOL spot trading insights.

Key Features:
- Coinalyze API: Precise funding rates, OI, liquidations, L/S ratios
- Sonar browsing: Fresh technical analysis, recent news (last hour only)
- Enhanced prompting: Robust technical pattern recognition
- Actionable insights: 3-5% move opportunities for spot trading
"""
from __future__ import annotations

import json
import math
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI

from whatsapp_sender import WhatsAppSender

# ---------------------------------------------------------------------------
# Environment & Constants
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Helper type aliases
# ---------------------------------------------------------------------------
History = List[float]
Snapshot = Dict[str, Any]


class SOLHybridAnalysis:  # pylint: disable=too-many-instance-attributes
    """Hybrid SOL analysis combining Coinalyze data with Sonar technical analysis."""

    COINALYZE_BASE_URL = "https://api.coinalyze.net/v1"

    def __init__(self) -> None:
        self.coinalyze_key = os.getenv("COINALYZE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.coinalyze_key:
            raise ValueError("COINALYZE_API_KEY required")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required")

        # Force Sonar model for hybrid analysis
        self.model_name = "perplexity/sonar-reasoning-pro"
        
        self.session = requests.Session()
        self.session.headers.update({"api_key": self.coinalyze_key})
        self.perp_symbol = "SOLUSDT_PERP.A"

    # ---------------------------------------------------------------------
    # Coinalyze Data Collection (Precise Derivatives Data)
    # ---------------------------------------------------------------------
    def _api_get(self, endpoint: str, params: Dict[str, Any] | None = None) -> Any:  # noqa: ANN401,E501
        """Wrapped GET with basic logging / error-handling."""
        url = f"{self.COINALYZE_BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            print(f"⚠️  API {endpoint} returned {response.status_code}")
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  API {endpoint} error: {exc}")
        return None

    def get_derivatives_snapshot(self) -> Snapshot:
        """Collect precise derivatives data from Coinalyze."""
        print("📊 Fetching precise derivatives data from Coinalyze...")
        now = int(time.time())

        # Price data
        current_price, price_24h_change, price_6h_change, price_history = self._collect_price(now)
        
        # Open Interest
        oi_usd, oi_24h_change, oi_6h_change, oi_history = self._collect_open_interest(now)
        
        # Funding rates (predicted removed)
        funding_rate, funding_6h_change, funding_history = self._collect_funding(now)
        
        # Long/Short ratios
        ls_ratio, ls_24h_avg, ls_24h_change, ls_6h_change, ls_history = self._collect_long_short(now)
        
        # Liquidations
        long_liq_24h, short_liq_24h, long_liq_6h, short_liq_6h, liq_6h_ratio = self._collect_liquidations(now)

        snapshot: Snapshot = {
            "timestamp": now,
            "price": current_price,
            "price_24h_change": price_24h_change,
            "price_6h_change": price_6h_change,
            "oi_usd": oi_usd,
            "oi_24h_change": oi_24h_change,
            "oi_6h_change": oi_6h_change,
            "funding_pct": funding_rate,
            "funding_6h_change": funding_6h_change,
            "ls_ratio": ls_ratio,
            "ls_24h_avg": ls_24h_avg,
            "ls_24h_change": ls_24h_change,
            "ls_6h_change": ls_6h_change,
            "long_liq_24h": long_liq_24h,
            "short_liq_24h": short_liq_24h,
            "long_liq_6h": long_liq_6h,
            "short_liq_6h": short_liq_6h,
            "liq_6h_ratio": liq_6h_ratio,
            "price_history": price_history,
            "oi_history": oi_history,
            "funding_history": funding_history,
            "ls_history": ls_history,
        }

        self._print_derivatives_summary(snapshot)
        return snapshot

    def _collect_price(self, now: int) -> Tuple[float, float, float, History]:
        current_price = price_24h_change = price_6h_change = 0.0
        price_history: History = []
        try:
            data = self._api_get(
                "/ohlcv-history",
                {
                    "symbols": self.perp_symbol,
                    "interval": "1hour",
                    "from": now - 24 * 3600,
                    "to": now,
                },
            )
            if data and data[0].get("history"):
                history = data[0]["history"]
                price_history = [float(h["c"]) for h in history]
                current_price = price_history[-1]
                price_24h_ago = price_history[0]
                price_24h_change = ((current_price - price_24h_ago) / price_24h_ago) * 100
                if len(price_history) > 6:
                    price_6h_ago = price_history[-7]
                    price_6h_change = ((current_price - price_6h_ago) / price_6h_ago) * 100
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  Price data error: {exc}")
        return current_price, price_24h_change, price_6h_change, price_history

    def _collect_open_interest(self, now: int) -> Tuple[float, float, float, History]:
        oi_usd = oi_24h_change = oi_6h_change = 0.0
        oi_history: History = []
        try:
            oi_snapshot = self._api_get(
                "/open-interest",
                {"symbols": self.perp_symbol, "convert_to_usd": "true"},
            )
            oi_usd = float(oi_snapshot[0]["value"]) if oi_snapshot else 0.0
            oi_hist_raw = self._api_get(
                "/open-interest-history",
                {
                    "symbols": self.perp_symbol,
                    "interval": "1hour",
                    "from": now - 24 * 3600,
                    "to": now,
                    "convert_to_usd": "true",
                },
            )
            if oi_hist_raw and oi_hist_raw[0].get("history"):
                history = oi_hist_raw[0]["history"]
                def _extract(record: Dict[str, Any]) -> float:  # noqa: ANN401
                    for key in ("c", "v", "value", "oi"):
                        if key in record:
                            return float(record[key])
                    return 0.0

                oi_history = [_extract(h) for h in history]
                oi_24h_ago = oi_history[0]
                oi_24h_change = ((oi_usd - oi_24h_ago) / oi_24h_ago) * 100 if oi_24h_ago else 0
                if len(oi_history) > 6:
                    oi_6h_ago = oi_history[-7]
                    oi_6h_change = ((oi_usd - oi_6h_ago) / oi_6h_ago) * 100 if oi_6h_ago else 0
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  Open-Interest data error: {exc}")
        return oi_usd, oi_24h_change, oi_6h_change, oi_history

    def _collect_funding(self, now: int) -> Tuple[float, float, History]:
        funding_rate = funding_6h_change = 0.0
        funding_history: History = []
        try:
            data_now = self._api_get("/funding-rate", {"symbols": self.perp_symbol})
            funding_rate = float(data_now[0]["value"]) * 100 if data_now else 0.0

            hist_raw = self._api_get(
                "/funding-rate-history",
                {
                    "symbols": self.perp_symbol,
                    "interval": "1hour",
                    "from": now - 24 * 3600,
                    "to": now,
                },
            )
            if hist_raw and hist_raw[0].get("history"):
                funding_history = [float(h.get("c", h.get("value", 0))) for h in hist_raw[0]["history"]]
                if len(funding_history) > 6:
                    funding_6h_ago = funding_history[-7] * 100  # stored as raw, convert to %
                    funding_6h_change = funding_rate - funding_6h_ago
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  Funding data error: {exc}")
        return (
            funding_rate,
            funding_6h_change,
            [v * 100 for v in funding_history],  # convert to percentage for display
        )

    def _collect_long_short(self, now: int) -> Tuple[float, float, float, float, History]:
        ls_ratio = ls_24h_avg = ls_24h_change = ls_6h_change = 0.0
        ls_history: History = []
        try:
            data = self._api_get(
                "/long-short-ratio-history",
                {
                    "symbols": self.perp_symbol,
                    "interval": "1hour",
                    "from": now - 24 * 3600,
                    "to": now,
                },
            )
            if data and data[0].get("history"):
                history = data[0]["history"]
                ls_history = [float(h.get("r", 0)) for h in history]
                ls_ratio = ls_history[-1]
                ls_24h_avg = statistics.mean(ls_history) if ls_history else 0.0
                ls_24h_ago = ls_history[0]
                ls_24h_change = ((ls_ratio - ls_24h_ago) / ls_24h_ago) * 100 if ls_24h_ago else 0
                if len(ls_history) > 6:
                    ls_6h_ago = ls_history[-7]
                    ls_6h_change = ((ls_ratio - ls_6h_ago) / ls_6h_ago) * 100 if ls_6h_ago else 0
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  Long/Short data error: {exc}")
        return ls_ratio, ls_24h_avg, ls_24h_change, ls_6h_change, ls_history

    def _collect_liquidations(self, now: int) -> Tuple[float, float, float, float, float]:
        long_liq_24h = short_liq_24h = long_liq_6h = short_liq_6h = 0.0
        try:
            data = self._api_get(
                "/liquidation-history",
                {
                    "symbols": self.perp_symbol,
                    "interval": "1hour",
                    "from": now - 24 * 3600,
                    "to": now,
                    "convert_to_usd": "true",
                },
            )
            if data and data[0].get("history"):
                history = data[0]["history"]
                for i, item in enumerate(history):
                    long_val = float(item.get("l", 0))
                    short_val = float(item.get("s", 0))
                    long_liq_24h += long_val
                    short_liq_24h += short_val
                    if i >= len(history) - 6:  # last 6 entries
                        long_liq_6h += long_val
                        short_liq_6h += short_val
        except Exception as exc:  # noqa: BLE001,E722
            print(f"⚠️  Liquidation data error: {exc}")
        total_24h = long_liq_24h + short_liq_24h
        total_6h = long_liq_6h + short_liq_6h
        liq_6h_ratio = (total_6h / total_24h) if total_24h else 0.0
        return long_liq_24h, short_liq_24h, long_liq_6h, short_liq_6h, liq_6h_ratio

    def _print_derivatives_summary(self, s: Snapshot) -> None:
        """Print derivatives data summary."""
        print(f"💰 Price: ${s['price']:.2f} ({s['price_24h_change']:+.1f}% 24h)")
        print(f"🏦 OI: ${s['oi_usd']/1e6:.1f}M ({s['oi_24h_change']:+.1f}% 24h)")
        print(f"💸 Funding: {s['funding_pct']:.3f}%")
        print(f"⚖️  L/S: {s['ls_ratio']:.2f} (avg: {s['ls_24h_avg']:.2f}, {s['ls_24h_change']:+.1f}%)")
        print(f"🔥 Liq: ${s['long_liq_24h']/1e6:.1f}M L / ${s['short_liq_24h']/1e6:.1f}M S")

    # ---------------------------------------------------------------------
    # Sonar Enhanced Analysis (Technical + Fresh News)
    # ---------------------------------------------------------------------
    def analyze_with_sonar(self, derivatives_data: Snapshot) -> str:
        """Enhanced analysis using Sonar for technical analysis and fresh news."""
        
        client = OpenAI(
            api_key=self.openai_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Format derivatives data for prompt
        def _csv(series: History, fmt: str) -> str:
            return ",".join(fmt.format(v) for v in series)

        derivatives_summary = (
            f"DERIVATIVES DATA (Coinalyze):\n"
            f"• Price: ${derivatives_data['price']:.2f} ({derivatives_data['price_24h_change']:+.1f}% 24h, {derivatives_data['price_6h_change']:+.1f}% 6h)\n"
            f"• Open Interest: ${derivatives_data['oi_usd']/1e6:.1f}M ({derivatives_data['oi_24h_change']:+.1f}% 24h, {derivatives_data['oi_6h_change']:+.1f}% 6h)\n"
            f"• Funding: {derivatives_data['funding_pct']:.3f}% (6h Δ {derivatives_data['funding_6h_change']:+.3f}%)\n"
            f"• Long/Short: {derivatives_data['ls_ratio']:.2f} (24h avg: {derivatives_data['ls_24h_avg']:.2f}, {derivatives_data['ls_24h_change']:+.1f}%)\n"
            f"• Liquidations: ${derivatives_data['long_liq_24h']/1e6:.1f}M longs / ${derivatives_data['short_liq_24h']/1e6:.1f}M shorts (24h)\n"
            f"• Price Series: [{_csv(derivatives_data['price_history'][-12:], '{:.2f}')}] (last 12h)\n"
            f"• OI Series: [{_csv(derivatives_data['oi_history'][-12:], '{:.0f}')}] (last 12h)\n"
        )

        # Enhanced prompt for hybrid analysis
        prompt = (
            f"{derivatives_summary}\n\n"
            
            "HYBRID ANALYSIS TASK:\n"
            "1. TECHNICAL ANALYSIS (CURRENT DATA ONLY):\n"
            "   - Browse SOL/USDT 1h & 4h charts for CURRENT price levels\n"
            "   - Find SUPPLY ZONES: Look for levels where price previously REJECTED DOWN with volume\n"
            "   - Find DEMAND ZONES: Look for levels where price previously BOUNCED UP with volume\n"
            "   - Identify ORDER BLOCKS: Large single candles that created strong moves\n"
            "   - Find LIQUIDITY ZONES: Round numbers, previous highs/lows where stops cluster\n"
            "   - Note current price relative to these REAL reaction zones\n"
            "   - IGNORE patterns, triangles, flags, historical patterns - focus ONLY on current price action\n"
            "   - CRITICAL: Do NOT reference previous analysis, historical context, or patterns from past data\n\n"
            
            "2. FRESH NEWS (Last Hour Only):\n"
            "   - Check CoinDesk, CryptoPanic, Decrypt for SOL news in LAST 60 MINUTES only\n"
            "   - Include only if directly impactful to SOL price\n"
            "   - Ignore older news or general crypto sentiment\n\n"
            

            
            "3. DERIVATIVES CORRELATION:\n"
            "   - Correlate the provided funding/OI/liquidation data with supply/demand zones\n"
            "   - Identify squeeze setups, distribution patterns, or funding stress\n\n"
            
            "FOCUS: Quick SOL trading analysis for WhatsApp updates\n\n"
            
            "RESPONSE FORMAT:\n"
            "🚨 SIGNAL: [LONG|SHORT|WAIT]\n"
            "📊 SETUP: [Brief technical + derivatives correlation]\n"
            "📰 NEWS: [Recent news or 'None']\n"
            "🎯 ENTRY: [Entry zone]\n"
            "⛔ STOP: [Stop loss]\n"
            "🎪 TARGET: [Target level]\n"
            "⚠️ RISK: [Key risk]"
        )

        system_prompt = (
            "You are a concise crypto analyst for WhatsApp updates. "
            "CRITICAL RULES:\n"
            "1. Only analyze CURRENT data provided\n"
            "2. Do NOT reference previous analysis, yesterday's data, or historical patterns\n"
            "3. Do NOT mention triangles, flags, or any chart patterns\n"
            "4. Focus ONLY on current price action and derivatives correlation\n"
            "5. Keep responses brief and actionable\n"
            "6. Only include news from the last 60 minutes\n"
            "7. Base analysis ONLY on the derivatives data and current chart levels provided"
        )

        print("🧠 Generating hybrid analysis with Sonar...")
        print("🔍 Technical analysis + fresh news + derivatives correlation...")

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/sol-hybrid-analysis",
                    "X-Title": "SOL Hybrid Technical Analysis",
                }
            )

            analysis = response.choices[0].message.content.strip() if response.choices[0].message.content else ""

            if not analysis:
                raise RuntimeError("Empty response from Sonar")

            print(f"✅ Hybrid analysis complete ({len(analysis)} chars)")
            return analysis

        except Exception as exc:  # noqa: BLE001,E722
            print(f"❌ Sonar analysis failed: {exc}")
            return (
                "🔍 TECHNICAL SETUP: Analysis unavailable due to technical issues\n"
                "📊 DERIVATIVES CORRELATION: Unable to correlate\n"
                "🌍 MACRO: Unable to check\n"
                "📰 FRESH NEWS (Last Hour): Unable to check\n"
                "🚨 SIGNAL: NO CLEAR SIGNAL\n"
                "🎯 ENTRY ZONES: Monitor manually\n"
                "⛔ STOP LOSS: Use backup analysis\n"
                "🎪 TARGET: Use backup analysis\n"
                "⚠️  RISK: High uncertainty"
            )

    # ---------------------------------------------------------------------
    # Output Formatting
    # ---------------------------------------------------------------------
    def format_hybrid_result(self, derivatives_data: Snapshot, analysis: str) -> str:
        """Format the complete hybrid analysis result."""
        # Return just the analysis without header and footer for concise WhatsApp messages
        return analysis

    # ---------------------------------------------------------------------
    # Main Execution
    # ---------------------------------------------------------------------
    def run_hybrid_analysis(self) -> str:
        """Execute the complete hybrid analysis."""
        print("🔥 SOL Hybrid Analysis Starting...")
        print("🎯 Combining Coinalyze derivatives + Sonar technical analysis")
        print("-" * 60)
        
        try:
            # Step 1: Get precise derivatives data from Coinalyze
            derivatives_data = self.get_derivatives_snapshot()
            
            # Step 2: Get enhanced technical analysis from Sonar
            analysis = self.analyze_with_sonar(derivatives_data)
            
            # Step 3: Format complete result
            result = self.format_hybrid_result(derivatives_data, analysis)
            
            print("\n📋 HYBRID ANALYSIS COMPLETE:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
            return result
            
        except Exception as exc:
            print(f"❌ Hybrid analysis failed: {exc}")
            return f"❌ Hybrid analysis failed: {exc}"


def main():
    """Run the hybrid analysis and send WhatsApp message."""
    try:
        analyzer = SOLHybridAnalysis()
        result = analyzer.run_hybrid_analysis()
        
        # Send to WhatsApp if enabled
        auto_send = os.getenv("AUTO_SEND_TO_WHATSAPP", "false").lower() == "true"
        if auto_send:
            print("\n📱 Sending analysis to WhatsApp...")
            try:
                from whatsapp_sender import WhatsAppSender
                sender = WhatsAppSender()
                if sender.send_message(result):
                    print("✅ WhatsApp message sent successfully!")
                else:
                    print("❌ Failed to send WhatsApp message")
            except Exception as whatsapp_error:
                print(f"❌ WhatsApp sending failed: {whatsapp_error}")
        else:
            print("\n📱 WhatsApp sending disabled (AUTO_SEND_TO_WHATSAPP=false)")
            
    except Exception as e:
        print(f"❌ Failed to run hybrid analysis: {e}")


if __name__ == "__main__":
    main()
