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
    # Feature Engineering for Reliable Signals
    # ---------------------------------------------------------------------
    @staticmethod
    def _safe_std(values: List[float]) -> float:
        if not values or len(values) < 2:
            return 0.0
        try:
            return statistics.pstdev(values)
        except Exception:
            return 0.0

    @staticmethod
    def _zscore_of_last(series: List[float]) -> float:
        if not series or len(series) < 3:
            return 0.0
        mean_val = statistics.mean(series[:-1])
        std_val = SOLHybridAnalysis._safe_std(series[:-1])
        if std_val == 0:
            return 0.0
        return (series[-1] - mean_val) / std_val

    @staticmethod
    def _pct_change(a: float, b: float) -> float:
        if b == 0:
            return 0.0
        return ((a - b) / b) * 100.0

    @staticmethod
    def _returns(series: List[float]) -> List[float]:
        if not series or len(series) < 2:
            return []
        returns: List[float] = []
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]
            if prev == 0:
                returns.append(0.0)
            else:
                returns.append((curr - prev) / prev)
        return returns

    def _assess_regime(self, price_history: History) -> Dict[str, Any]:
        regime: Dict[str, Any] = {"trend": "side", "volatility": "normal", "chop": False}
        if not price_history or len(price_history) < 8:
            return regime
        # Trend via short (4h) vs long (12h) moving averages
        short_ma = statistics.mean(price_history[-4:])
        long_ma = statistics.mean(price_history[-12:]) if len(price_history) >= 12 else statistics.mean(price_history)
        if short_ma > long_ma * 1.001:
            regime["trend"] = "up"
        elif short_ma < long_ma * 0.999:
            regime["trend"] = "down"
        else:
            regime["trend"] = "side"
        # Volatility via stdev of 1h returns (last 24 samples if available)
        rets = self._returns(price_history[-25:])
        vol = self._safe_std(rets)
        # Simple bands for low/normal/high
        if vol < 0.002:
            regime["volatility"] = "low"
        elif vol > 0.008:
            regime["volatility"] = "high"
        else:
            regime["volatility"] = "normal"
        # Chop if low vol and side trend
        regime["chop"] = (regime["volatility"] == "low" and regime["trend"] == "side")
        return regime

    def _detect_divergences(self, s: Snapshot) -> List[str]:
        notes: List[str] = []
        p6 = s.get("price_6h_change", 0.0)
        oi6 = s.get("oi_6h_change", 0.0)
        f6 = s.get("funding_6h_change", 0.0)
        # Price up but OI down => short covering
        if p6 > 0.5 and oi6 < -0.5:
            notes.append("Price↑ + OI↓ (short covering)")
        # Price down but OI up => aggressive shorts
        if p6 < -0.5 and oi6 > 0.5:
            notes.append("Price↓ + OI↑ (new shorts)")
        # Funding stress vs price
        if p6 > 0.5 and f6 < -0.01:
            notes.append("Price↑ + Funding↓ (stress)")
        if p6 < -0.5 and f6 > 0.01:
            notes.append("Price↓ + Funding↑ (stress)")
        return notes

    def _compute_confidence(self, s: Snapshot, regime: Dict[str, Any], z: Dict[str, float], divergences: List[str]) -> Tuple[int, str, List[str]]:
        long_score = 50
        short_score = 50
        drivers: List[str] = []
        # Alignment: price vs OI
        p6 = s.get("price_6h_change", 0.0)
        oi6 = s.get("oi_6h_change", 0.0)
        if p6 > 0.5 and oi6 > 0.5:
            long_score += 15; drivers.append("Price↑ + OI↑ (continuation)")
        if p6 < -0.5 and oi6 < -0.5:
            short_score += 15; drivers.append("Price↓ + OI↓ (continuation)")
        # Funding supports direction
        funding = s.get("funding_pct", 0.0)
        if funding > 0.02:
            long_score += 10; drivers.append("Funding positive")
        if funding < -0.02:
            short_score += 10; drivers.append("Funding negative")
        # L/S extremes penalize crowded side
        ls = s.get("ls_ratio", 0.0)
        if ls > 3.0:
            short_score += 5; drivers.append("Crowded longs (L/S>")
        if ls < 1.0 and ls > 0:
            long_score += 5; drivers.append("Crowded shorts (L/S<)")
        # Regime filters
        if regime.get("trend") == "up":
            long_score += 5
        if regime.get("trend") == "down":
            short_score += 5
        if regime.get("chop"):
            long_score -= 5; short_score -= 5; drivers.append("Chop regime")
        # Divergences reduce confidence in directional calls
        if divergences:
            long_score -= 5; short_score -= 5; drivers.extend(divergences)
        # Compose signal
        delta = long_score - short_score
        if delta > 10:
            auto = "LONG"
            conf = min(100, max(0, long_score))
        elif delta < -10:
            auto = "SHORT"
            conf = min(100, max(0, short_score))
        else:
            auto = "WAIT"
            conf = min(100, max(0, 50 - abs(delta)))
        return int(conf), auto, drivers[:4]

    def _compute_features(self, s: Snapshot) -> Dict[str, Any]:
        # Z-scores for last values
        z_funding = self._zscore_of_last(s.get("funding_history", []) or [])
        z_oi = self._zscore_of_last(s.get("oi_history", []) or [])
        z_ls = self._zscore_of_last(s.get("ls_history", []) or [])
        regime = self._assess_regime(s.get("price_history", []) or [])
        divergences = self._detect_divergences(s)
        z = {"funding": z_funding, "oi": z_oi, "ls": z_ls}
        confidence, auto_signal, drivers = self._compute_confidence(s, regime, z, divergences)
        # Build compact summary
        feats_lines = [
            f"Z(funding)={z_funding:+.2f}, Z(oi)={z_oi:+.2f}, Z(ls)={z_ls:+.2f}",
            f"Regime: trend={regime['trend']}, vol={regime['volatility']}, chop={regime['chop']}",
        ]
        if drivers:
            feats_lines.append("Drivers: " + "; ".join(drivers))
        if divergences:
            feats_lines.append("Divergences: " + "; ".join(divergences))
        return {
            "summary": "\n".join(feats_lines),
            "confidence": confidence,
            "auto_signal": auto_signal,
            "drivers": drivers,
        }

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

        # Compute features and confidence
        features = self._compute_features(derivatives_data)
        features_block = (
            "FEATURES:\n"
            f"{features['summary']}\n"
            f"Auto: {features['auto_signal']} | Confidence: {features['confidence']}/100\n"
        )

                    # Enhanced prompt for hybrid analysis with better insights
            prompt = (
                f"{derivatives_summary}\n\n"
                f"{features_block}\n"
                f"CURRENT TIME: {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n"
                
                "ENHANCED HYBRID ANALYSIS TASK:\n"
                "1. TECHNICAL ANALYSIS (ACTIONABLE INSIGHTS):\n"
                "   - Analyze SOL/USDT current price action and key levels\n"
                "   - Identify IMMEDIATE support/resistance within 2-3% of current price\n"
                "   - Find ORDER FLOW signals: volume spikes, rejection wicks, breakout patterns\n"
                "   - Determine MARKET STRUCTURE: trending, ranging, or transitional\n"
                "   - Focus on TRADEABLE setups for next 4-24 hours\n"
                "   - Provide SPECIFIC price levels for entries, stops, targets\n\n"
                
                "2. DERIVATIVES INSIGHT:\n"
                "   - Correlate funding rates with price momentum (funding stress = reversal risk)\n"
                "   - Analyze OI changes: increasing OI + price up = strong trend, decreasing = weakness\n"
                "   - Use L/S ratio for contrarian signals: extreme ratios often precede reversals\n"
                "   - Identify FUNDING SQUEEZE potential or OI liquidation zones\n\n"
                
                "3. RISK ASSESSMENT:\n"
                "   - Evaluate volatility based on recent price action\n"
                "   - Identify key risk factors: funding stress, OI extremes, news events\n"
                "   - Determine position sizing recommendation based on setup quality\n\n"
                
                "FOCUS: Actionable trading insights for SOL spot trading\n\n"
                
                "RESPONSE FORMAT (BE SPECIFIC AND ACTIONABLE):\n"
                "🚨 SIGNAL: [LONG|SHORT|WAIT]\n"
                "📊 SETUP: [Specific technical pattern + key levels]\n"
                "🎯 ENTRY: [Exact entry price/zone]\n"
                "⛔ STOP: [Specific stop loss level]\n"
                "🎪 TARGET: [Primary target with reasoning]\n"
                "⚠️ RISK: [Main risk factor + mitigation]\n"
                "📈 TIMEFRAME: [Expected move duration]\n"
                "💡 CONTEXT: [Market condition summary]"
            )

                    system_prompt = (
                "You are an expert crypto analyst providing actionable SOL trading insights. "
                "CRITICAL REQUIREMENTS:\n"
                "1. ACTIONABLE INSIGHTS: Provide specific, tradeable information\n"
                "2. PRECISE LEVELS: Give exact entry, stop, and target prices\n"
                "3. RISK CLARITY: Clearly state main risks and how to manage them\n"
                "4. TIMEFRAME SPECIFIC: Indicate expected move duration (hours/days)\n"
                "5. CONTEXT AWARE: Explain WHY the setup works based on derivatives data\n"
                "6. NO VAGUE LANGUAGE: Avoid 'monitor', 'watch' - give specific actions\n"
                "7. MARKET STRUCTURE: Identify if trending, ranging, or transitional\n"
                "8. POSITION SIZING: Suggest appropriate risk level based on setup quality"
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
        """Format the complete hybrid analysis result with enhanced insights."""
        try:
            features = self._compute_features(derivatives_data)
            
            # Enhanced market context
            price_momentum = "bullish" if derivatives_data['price_24h_change'] > 1 else "bearish" if derivatives_data['price_24h_change'] < -1 else "neutral"
            oi_trend = "expanding" if derivatives_data['oi_24h_change'] > 2 else "contracting" if derivatives_data['oi_24h_change'] < -2 else "stable"
            funding_stress = "high" if abs(derivatives_data['funding_pct']) > 0.05 else "normal"
            
            # Create enhanced structured format for better WhatsApp parsing
            structured_analysis = (
                f"MARKET DATA:\n"
                f"Price: ${derivatives_data['price']:.2f} ({derivatives_data['price_24h_change']:+.1f}% 24h)\n"
                f"OI: ${derivatives_data['oi_usd']/1e6:.1f}M ({derivatives_data['oi_24h_change']:+.1f}%)\n"
                f"Funding: {derivatives_data['funding_pct']:.3f}% (6h Δ {derivatives_data['funding_6h_change']:+.3f}%)\n"
                f"L/S: {derivatives_data['ls_ratio']:.2f}\n\n"
                f"MARKET CONTEXT:\n"
                f"Momentum: {price_momentum.title()}\n"
                f"OI Trend: {oi_trend.title()}\n"
                f"Funding Stress: {funding_stress.title()}\n"
                f"Auto Signal: {features['auto_signal']}\n"
                f"Confidence: {features['confidence']}/100\n\n"
                f"ANALYSIS:\n"
                f"{analysis}\n\n"
                f"KEY INSIGHTS:\n"
                f"- Price momentum is {price_momentum} with {oi_trend} open interest\n"
                f"- Funding stress level: {funding_stress}\n"
                f"- L/S ratio at {derivatives_data['ls_ratio']:.2f} indicates {'crowded longs' if derivatives_data['ls_ratio'] > 2.5 else 'balanced positioning' if derivatives_data['ls_ratio'] > 1.5 else 'crowded shorts'}\n"
                f"- Confidence level: {features['confidence']}/100 based on signal alignment"
            )
            
            return structured_analysis
            
        except Exception as e:
            print(f"⚠️  Format error: {e}")
            return f"MARKET DATA:\nPrice: ${derivatives_data.get('price', 0):.2f}\nAnalysis: {analysis}"

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
    """Run the hybrid analysis and send WhatsApp message with comprehensive error handling."""
    print("🚀 Starting SOL Hybrid Analysis with robust error handling...")
    
    # ROBUST ERROR HANDLING: Environment validation
    required_env_vars = ['COINALYZE_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("💡 Please set these variables in your environment or .env file")
        return False
    
    try:
        # ROBUST INITIALIZATION: Create analyzer with validation
        print("🔧 Initializing SOL Hybrid Analysis...")
        analyzer = SOLHybridAnalysis()
        
        # ROBUST ANALYSIS: Run with comprehensive error handling
        print("📈 Running hybrid analysis...")
        result = analyzer.run_hybrid_analysis()
        
        if not result or len(result.strip()) < 50:
            print("⚠️  Analysis result seems incomplete or empty")
            print(f"Result length: {len(result) if result else 0} characters")
            return False
        
        print(f"✅ Analysis completed successfully ({len(result)} characters)")
        
        # ROBUST WHATSAPP HANDLING: Check if WhatsApp sending is enabled
        auto_send = os.getenv("AUTO_SEND_TO_WHATSAPP", "false").lower() == "true"
        if auto_send:
            return _send_whatsapp_with_robust_handling(result)
        else:
            print("\n📱 WhatsApp sending disabled (AUTO_SEND_TO_WHATSAPP=false)")
            print("💡 Set AUTO_SEND_TO_WHATSAPP=true to enable automatic sending")
            return True
            
    except Exception as e:
        print(f"❌ Critical error in main analysis: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        import traceback
        print(f"💡 Traceback: {traceback.format_exc()}")
        return False


def _send_whatsapp_with_robust_handling(result: str) -> bool:
    """Handle WhatsApp sending with comprehensive error handling and validation."""
    print("\n📱 Starting robust WhatsApp sending process...")
    
    # ROBUST VALIDATION: Check WhatsApp environment
    whatsapp_env_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_FROM', 'TWILIO_TEMPLATE_SID']
    missing_whatsapp_vars = [var for var in whatsapp_env_vars if not os.getenv(var)]
    
    if missing_whatsapp_vars:
        print(f"❌ Missing WhatsApp environment variables: {missing_whatsapp_vars}")
        print("\n💡 WhatsApp Setup Required:")
        for var in missing_whatsapp_vars:
            print(f"   - Set {var} in GitHub Secrets")
        print("   - See WHATSAPP_TEMPLATE_SETUP.md for detailed instructions")
        return False
    
    # ROBUST VALIDATION: Check recipients
    recipients = os.getenv('WHATSAPP_TO_NUMBERS') or os.getenv('WHATSAPP_TO_NUMBER')
    if not recipients:
        print("❌ No WhatsApp recipients configured")
        print("💡 Set WHATSAPP_TO_NUMBERS or WHATSAPP_TO_NUMBER environment variable")
        return False
    
    # Debug: Show configuration status
    template_sid = os.getenv("TWILIO_TEMPLATE_SID")
    print(f"✅ Template SID configured: {template_sid[:10]}...{template_sid[-10:]}")
    print(f"✅ Recipients configured: {len(recipients.split(','))} numbers")
    
    try:
        # ROBUST IMPORT: Import WhatsApp sender with error handling
        try:
            from whatsapp_sender import WhatsAppSender
        except ImportError as import_error:
            print(f"❌ Failed to import WhatsAppSender: {import_error}")
            print("💡 Check if Twilio library is installed: pip install twilio")
            return False
        
        # ROBUST INITIALIZATION: Create sender with validation
        print("🔧 Initializing WhatsApp sender...")
        sender = WhatsAppSender()
        
        if not sender.client:
            print("❌ WhatsApp sender initialization failed")
            return False
        
        # ROBUST DATA PREPARATION: Create analysis data structure
        analysis_data = {
            'analysis': result,
            'model_used': 'Sonar Hybrid (Robust)',
            'timestamp': datetime.now().strftime('%H:%M UTC')
        }
        
        # ROBUST TESTING: Pre-validate template extraction
        print("💬 Pre-validating template variable extraction...")
        try:
            test_message, test_vars = sender._create_whatsapp_summary(
                result, 'Sonar Hybrid', datetime.now().strftime('%H:%M UTC')
            )
            
            # Validate template variables
            if not sender._validate_template_vars(test_vars):
                print("❌ Template variable pre-validation failed")
                return False
            
            print(f"✅ Template pre-validation successful")
            print(f"   - Variables extracted: {len(test_vars)}")
            print(f"   - Message length: {len(test_message)} characters")
            
            # Show key variables for debugging
            key_vars = ['2', '3', '4', '9', '10']
            print("🔍 Key extracted variables:")
            for var in key_vars:
                value = test_vars.get(var, 'N/A')
                display_value = value[:30] + '...' if len(str(value)) > 30 else value
                print(f"   {var}: {display_value}")
            
        except Exception as template_error:
            print(f"❌ Template variable pre-validation failed: {template_error}")
            print("💡 Analysis format may be incompatible with template extraction")
            return False
        
        # ROBUST SENDING: Send with comprehensive error handling
        print("🚀 Sending WhatsApp message with robust error handling...")
        success = sender.send_analysis_summary(analysis_data)
        
        if success:
            print("✅ WhatsApp message sent successfully with robust handling!")
            print("🎉 All systems operational - message delivered")
            return True
        else:
            print("❌ WhatsApp message sending failed despite robust handling")
            print("\n💡 Final troubleshooting steps:")
            print("   1. Verify template approval status in Twilio Console")
            print("   2. Test with your own WhatsApp number first")
            print("   3. Check phone number format (+country_code)")
            print("   4. Ensure template variables match exactly")
            print("   5. See WHATSAPP_DELIVERY_TROUBLESHOOTING.md")
            return False
            
    except Exception as whatsapp_error:
        print(f"❌ Unexpected WhatsApp error: {whatsapp_error}")
        print(f"💡 Error type: {type(whatsapp_error).__name__}")
        import traceback
        print(f"💡 Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 SOL Hybrid Analysis completed successfully!")
            exit(0)
        else:
            print("\n❌ SOL Hybrid Analysis failed")
            exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)
