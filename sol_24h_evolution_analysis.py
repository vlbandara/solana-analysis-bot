#!/usr/bin/env python3
"""
SOL Hourly Update Analysis
==========================
This script analyses the evolution of Solana perpetual futures market data over the
last 24 hours (for context) and provides hourly updates focused on short-term spot trading opportunities (3-5% moves).
Key modifications:
------------------
1. Removed daily report integration for a fresh market perspective.
2. Enhanced focus on technicals: expanded prompt instructions for deeper SOL chart analysis (e.g., patterns, indicators like RSI, MACD, support/resistance, volume).
3. Retained browsing for BTC dominance, DXY, news, and chart analysis.
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
class SolHourlyUpdateAnalysis: # pylint: disable=too-many-instance-attributes
    """Analyse SOL perpetual futures for hourly spot trading signals."""
    COINALYZE_BASE_URL = "https://api.coinalyze.net/v1"
    def __init__(self) -> None:
        self.coinalyze_key = os.getenv("COINALYZE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.coinalyze_key:
            raise ValueError("COINALYZE_API_KEY required")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required")
        # Model selection: assumes Sonar with browsing (e.g., 'perplexity/sonar-reasoning-pro')
        self.model_name = os.getenv("LLM_MODEL", "perplexity/sonar-reasoning-pro")
        self.session = requests.Session()
        self.session.headers.update({"api_key": self.coinalyze_key})
        self.perp_symbol = "SOLUSDT_PERP.A"
    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _api_get(self, endpoint: str, params: Dict[str, Any] | None = None) -> Any: # noqa: ANN401,E501
        """Wrapped GET with basic logging / error-handling."""
        url = f"{self.COINALYZE_BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            print(f"⚠️ API {endpoint} returned {response.status_code}")
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ API {endpoint} error: {exc}")
        return None
    # ---------------------------------------------------------------------
    # Data acquisition & processing
    # ---------------------------------------------------------------------
    def get_current_snapshot(self) -> Snapshot: # noqa: C901, PLR0915, PLR0912, PLR0913, PLR0914
        """Collect market data & derive enriched snapshot and historical series."""
        print("📊 Fetching comprehensive SOL data (24h evolution for hourly update) …")
        now = int(time.time())
        # ------------------------- Price ----------------------------------
        (current_price,
         price_24h_change,
         price_6h_change,
         price_history) = self._collect_price(now)
        # ------------------------- Open Interest --------------------------
        (
            oi_usd,
            oi_24h_change,
            oi_6h_change,
            oi_history,
        ) = self._collect_open_interest(now)
        # ------------------------- Funding Rate ---------------------------
        (
            funding_rate,
            predicted_funding_rate,
            funding_6h_change,
            funding_history,
            funding_predicted_diff,
        ) = self._collect_funding(now)
        # ------------------------- Long / Short Ratio ---------------------
        (
            ls_ratio,
            ls_24h_avg,
            ls_24h_change,
            ls_6h_change,
            ls_history,
        ) = self._collect_long_short(now)
        # ------------------------- Liquidations ---------------------------
        (
            long_liq_24h,
            short_liq_24h,
            long_liq_6h,
            short_liq_6h,
            liq_6h_ratio,
        ) = self._collect_liquidations(now)
        # -----------------------------------------------------------------
        # Assemble snapshot
        # -----------------------------------------------------------------
        snapshot: Snapshot = {
            # timestamp
            "timestamp": now,
            # price
            "price": current_price,
            "price_24h_change": price_24h_change,
            "price_6h_change": price_6h_change,
            # open interest
            "oi_usd": oi_usd,
            "oi_24h_change": oi_24h_change,
            "oi_6h_change": oi_6h_change,
            # funding
            "funding_pct": funding_rate,
            "predicted_funding_pct": predicted_funding_rate,
            "funding_6h_change": funding_6h_change,
            "funding_predicted_diff": funding_predicted_diff,
            # long/short
            "ls_ratio": ls_ratio,
            "ls_24h_avg": ls_24h_avg,
            "ls_24h_change": ls_24h_change,
            "ls_6h_change": ls_6h_change,
            # liquidations
            "long_liq_24h": long_liq_24h,
            "short_liq_24h": short_liq_24h,
            "long_liq_6h": long_liq_6h,
            "short_liq_6h": short_liq_6h,
            "liq_6h_ratio": liq_6h_ratio,
            # series (compact)
            "price_history": price_history,
            "oi_history": oi_history,
            "funding_history": funding_history,
            "ls_history": ls_history,
        }
        # Pretty print summary
        self._pretty_print_snapshot(snapshot)
        return snapshot
    # ------------------------------------------------------------------
    # Section-specific collectors
    # ------------------------------------------------------------------
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
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ Price data error: {exc}")
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
                # choose the most appropriate key for value
                def _extract(record: Dict[str, Any]) -> float: # noqa: ANN401
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
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ Open-Interest data error: {exc}")
        return oi_usd, oi_24h_change, oi_6h_change, oi_history
    def _collect_funding(self, now: int) -> Tuple[float, float, float, History, float]:
        funding_rate = predicted_funding_rate = funding_6h_change = 0.0
        funding_predicted_diff = 0.0
        funding_history: History = []
        try:
            data_now = self._api_get("/funding-rate", {"symbols": self.perp_symbol})
            funding_rate = float(data_now[0]["value"]) * 100 if data_now else 0.0
            data_pred = self._api_get("/predicted-funding-rate", {"symbols": self.perp_symbol})
            predicted_funding_rate = float(data_pred[0]["value"]) * 100 if data_pred else 0.0
            funding_predicted_diff = predicted_funding_rate - funding_rate
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
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ Funding data error: {exc}")
        return (
            funding_rate,
            predicted_funding_rate,
            funding_6h_change,
            [v * 100 for v in funding_history],  # convert to percentage for display
            funding_predicted_diff,
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
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ Long/Short data error: {exc}")
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
        except Exception as exc: # noqa: BLE001,E722
            print(f"⚠️ Liquidation data error: {exc}")
        total_24h = long_liq_24h + short_liq_24h
        total_6h = long_liq_6h + short_liq_6h
        liq_6h_ratio = (total_6h / total_24h) if total_24h else 0.0
        return long_liq_24h, short_liq_24h, long_liq_6h, short_liq_6h, liq_6h_ratio
    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _pretty_print_snapshot(s: Snapshot) -> None: # noqa: D401
        """Print a human friendly one-liner summary to STDOUT."""
        print(
            f" 💰 Price: ${s['price']:.2f} ({s['price_24h_change']:+.1f}% 24h)"
        )
        print(
            f" 🏦 OI: ${s['oi_usd']/1e6:.1f}M ({s['oi_24h_change']:+.1f}% 24h)"
        )
        print(
            f" 💸 Funding: {s['funding_pct']:.3f}% (pred: {s['predicted_funding_pct']:.3f}%)"
        )
        print(
            f" ⚖️ L/S: {s['ls_ratio']:.2f} (24h avg: {s['ls_24h_avg']:.2f}, {s['ls_24h_change']:+.1f}%)"
        )
        print(
            " 🔥 Liq 24h: "
            f"${s['long_liq_24h']/1e6:.1f}M L / ${s['short_liq_24h']/1e6:.1f}M S"
        )
        print(
            " 🔥 Liq 6h: "
            f"${s['long_liq_6h']/1e6:.1f}M L / ${s['short_liq_6h']/1e6:.1f}M S"
        )
    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze_with_reasoning(self, current: Snapshot, last: Snapshot | None = None) -> str: # noqa: C901, PLR0915,E501
        """Generate comprehensive reasoning with enhanced prompt for browsing and technicals."""
        # Dynamically select provider based on model name
        if self.model_name.startswith("perplexity/"):
            client = OpenAI(
                api_key=self.openai_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            client = OpenAI(api_key=self.openai_key)
        # --------------------------------------------------------------
        # Change vs previous run (if provided)
        # --------------------------------------------------------------
        changes_block = ""
        if last:
            def _pct(new: float, old: float) -> float:
                return ((new - old) / old * 100) if old else 0.0
            changes_block = (
                "\nCHANGES SINCE LAST RUN:"\
                f"\n• Price: {_pct(current['price'], last['price']):+.1f}%"\
                f"\n• OI: {_pct(current['oi_usd'], last['oi_usd']):+.1f}%"\
                f"\n• Funding: {current['funding_pct'] - last['funding_pct']:+.3f}%"\
                f"\n• L/S Ratio: {_pct(current['ls_ratio'], last['ls_ratio']):+.1f}%\n"
            )
        # --------------------------------------------------------------
        # Compact CSV-style historical sequences (easier for LLM to parse)
        # --------------------------------------------------------------
        def _csv(series: History, fmt: str) -> str:
            return ",".join(fmt.format(v) for v in series)
        history_block = (
            "DATA EVOLUTION (hourly series ‑ newest last):"\
            f"\nprice_usd=[{_csv(current['price_history'], '{:.2f}')} ]"\
            f"\noi_usd=[{_csv(current['oi_history'], '{:.0f}')} ]"\
            f"\nfunding_pct=[{_csv(current['funding_history'], '{:.4f}')} ]"\
            f"\nls_ratio=[{_csv(current['ls_history'], '{:.2f}')} ]\n"
        )
        # --------------------------------------------------------------
        # Prompt construction (enhanced for technical focus, no daily report)
        # --------------------------------------------------------------
        prompt = (
            "SNAPSHOT:"\
            f"\n• Price: ${current['price']:.2f} ({current['price_24h_change']:+.1f}% 24h, {current['price_6h_change']:+.1f}% 6h)"\
            f"\n• OI: ${current['oi_usd']/1e6:.1f}M ({current['oi_24h_change']:+.1f}% 24h, {current['oi_6h_change']:+.1f}% 6h)"\
            f"\n• Funding: {current['funding_pct']:.3f}% → {current['predicted_funding_pct']:.3f}% (6h Δ {current['funding_6h_change']:+.3f}%, pred Δ {current['funding_predicted_diff']:+.3f}%)"\
            f"\n• L/S: {current['ls_ratio']:.2f} (24h Δ {current['ls_24h_change']:+.1f}%, 6h Δ {current['ls_6h_change']:+.1f}%)"\
            f"\n• Liq: 24h ${current['long_liq_24h']/1e6:.1f}M L / ${current['short_liq_24h']/1e6:.1f}M S (6h/24h ratio {current['liq_6h_ratio']:.2f})"\
            f"\n{changes_block}\n"
            f"{history_block}"
            "\nTASK:"\
            " Use browsing to fetch: current BTC dominance (%), DXY dollar index value. "
            "Deeply analyze SOL 1h/4h charts for technicals: identify patterns (e.g., triangles, flags, head & shoulders), key levels (support/resistance), indicators (RSI, MACD, EMA crossovers, volume trends, divergences). "
            "Check for major news on SOL or BTC in the last hour (e.g., via CoinDesk, CryptoPanic); include only if impactful. "
            "Interpret market data for short-term SOL spot trades (3-5% moves), focusing on derivatives signals (funding, OI, liqs, L/S) and momentum, with emphasis on technicals for fresh perspective. "
            "Emphasize detecting drop risks (e.g., like past crash to 160). Identify divergences, shifts, leverage stress. "
            "Incorporate BTC dom/DXY for macro context. Keep concise, actionable for buy/sell/exit.\n"
            "\nRESPONSE FORMAT (copy exactly):\n"\
            "🚨 SIGNAL: <PUMP RISK|DROP RISK|SQUEEZE SETUP|NO CLEAR SIGNAL>\n"\
            "📊 CORRELATION: <Key relationships, incl. BTC dom, DXY, SOL techs>\n"\
            "📰 NEWS: <Brief major news if any; else 'None'>\n"\
            "⚠️ POSITIONED: <Warning for longs/shorts with levels>\n"\
            "💡 PREPARE: <How to hedge/position for 3-5% move>"
        )
        system_prompt = (
            "You are an elite derivatives analyst (role: Analyst) collaborating with a "
            "risk-strategist (role: Strategist). As Analyst: parse data, detect patterns, browse for real-time info, and "
            "explain correlations succinctly with focus on technicals. As Strategist: translate insights into actionable "
            "guidance. Always comply with the response format. Use browsing only as instructed."
        )
        print(f"🧠 Calling {self.model_name} model for analysis …")
        print(f"🔍 Prompt length: {len(prompt)} chars")
        try:
            # Add extra headers for OpenRouter if using perplexity model
            extra_kwargs = {}
            if self.model_name.startswith("perplexity/"):
                extra_kwargs["extra_headers"] = {
                    "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://github.com/your-repo"),
                    "X-Title": os.getenv("OPENROUTER_TITLE", "SOL Analysis Tool"),
                }
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                **extra_kwargs
            )
            analysis = (
                response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            )
            if not analysis:
                raise RuntimeError("Empty response from LLM")
            print(f"✅ Analysis received ({len(analysis)} chars)")
            return analysis
        except Exception as exc: # noqa: BLE001,E722
            print(f"❌ Model failed: {exc}")
            return (
                "🚨 SIGNAL: NO CLEAR SIGNAL\n"
                "📊 CORRELATION: Analysis unavailable due to technical issues\n"
                "📰 NEWS: None\n"
                "⚠️ POSITIONED: Monitor market manually\n"
                "💡 PREPARE: Use backup analysis tools"
            )
    # ------------------------------------------------------------------
    # WhatsApp formatting & sending
    # ------------------------------------------------------------------
    @staticmethod
    def format_whatsapp(analysis_json: str, data: Snapshot) -> str: # noqa: D401
        """Generate WhatsApp-friendly message with header and model response."""
        utc_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
        header = (
            f"🎯 SOL Hourly • {utc_time}\n"
            f"📊 ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h) | "
            f"OI: ${data['oi_usd']/1e6:.1f}M ({data['oi_24h_change']:+.1f}%)\n"
            f"💸 {data['funding_pct']:.3f}% → {data['predicted_funding_pct']:.3f}% | "
            f"L/S: {data['ls_ratio']:.2f}\n\n"
        )
        return header + analysis_json + "\n\n📈 Hourly update • Sonar"
    # ------------------------------------------------------------------
    # Public orchestrator
    # ------------------------------------------------------------------
    def run(self) -> None: # noqa: C901
        """Main workflow."""
        print("🚀 SOL Hourly Update Analysis starting …")
        try:
            current = self.get_current_snapshot()
            should_send = True  # can be extended with state tracking later
            if not should_send:
                print("ℹ️ No significant changes – alert suppressed")
                return
            print("🧠 Generating LLM analysis …")
            analysis_json = self.analyze_with_reasoning(current)
            whatsapp_msg = self.format_whatsapp(analysis_json, current)
            print("📱 WhatsApp message preview:")
            print("-" * 60)
            print(whatsapp_msg)
            print("-" * 60)
            if os.getenv("AUTO_SEND_TO_WHATSAPP", "true").lower() == "true":
                recipients_env = os.getenv("WHATSAPP_TO_NUMBERS") or os.getenv("WHATSAPP_TO_NUMBER", "")
                recipients = [p.strip() for p in recipients_env.split(",") if p.strip()]
                if not recipients:
                    print("⚠️ No WhatsApp recipients configured")
                else:
                    sender = WhatsAppSender()
                    delivered, failed = [], []
                    for phone in recipients:
                        sender.to_number = phone  # override target dynamically
                        if sender.send_message(whatsapp_msg):
                            delivered.append(phone)
                        else:
                            failed.append(phone)
                    if delivered:
                        print(f"✅ Delivered to: {', '.join(delivered)}")
                    if failed:
                        print(f"⚠️ Failed to deliver to: {', '.join(failed)}")
            else:
                print("📱 AUTO_SEND_TO_WHATSAPP disabled")
        except Exception as exc: # noqa: BLE001,E722
            print(f"❌ Analysis failed: {exc}")
            import traceback  # lazy import for error path only
            traceback.print_exc()
# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
def main() -> None: # noqa: D401
    """Entry-point wrapper."""
    SolHourlyUpdateAnalysis().run()
if __name__ == "__main__":
    main()