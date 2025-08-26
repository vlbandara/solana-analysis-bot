#!/usr/bin/env python3
"""
SOL Spot Trader - Concise Analysis for 2-5% Gains
=================================================
Quick, actionable SOL spot trading analysis combining derivatives data with technical levels.
Focused on spot trader needs: clear entry/exit levels for 2-5% gains.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class SOLSpotTrader:
    """Concise SOL spot trading analysis for 2-5% gains."""
    
    COINALYZE_BASE_URL = "https://api.coinalyze.net/v1"
    
    def __init__(self):
        self.coinalyze_key = os.getenv("COINALYZE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.coinalyze_key or not self.openai_key:
            raise ValueError("Both COINALYZE_API_KEY and OPENAI_API_KEY required")
        
        self.session = requests.Session()
        self.session.headers.update({"api_key": self.coinalyze_key})
        self.perp_symbol = "SOLUSDT_PERP.A"
    
    def get_derivatives_data(self) -> Dict[str, Any]:
        """Get key derivatives data from Coinalyze."""
        now = int(time.time())
        
        # Price
        price_data = self._api_get("/ohlcv-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": now - 24 * 3600,
            "to": now,
        })
        
        current_price = 0.0
        price_24h_change = 0.0
        if price_data and price_data[0].get("history"):
            history = price_data[0]["history"]
            prices = [float(h["c"]) for h in history]
            current_price = prices[-1]
            price_24h_change = ((current_price - prices[0]) / prices[0]) * 100
        
        # OI
        oi_data = self._api_get("/open-interest", {
            "symbols": self.perp_symbol,
            "convert_to_usd": "true"
        })
        oi_usd = float(oi_data[0]["value"]) if oi_data else 0.0
        
        # Funding
        funding_data = self._api_get("/funding-rate", {"symbols": self.perp_symbol})
        funding_rate = float(funding_data[0]["value"]) * 100 if funding_data else 0.0
        
        pred_funding_data = self._api_get("/predicted-funding-rate", {"symbols": self.perp_symbol})
        pred_funding = float(pred_funding_data[0]["value"]) * 100 if pred_funding_data else 0.0
        
        # L/S Ratio
        ls_data = self._api_get("/long-short-ratio-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": now - 24 * 3600,
            "to": now,
        })
        ls_ratio = 0.0
        ls_24h_change = 0.0
        if ls_data and ls_data[0].get("history"):
            ls_history = [float(h.get("r", 0)) for h in ls_data[0]["history"]]
            ls_ratio = ls_history[-1]
            ls_24h_change = ((ls_ratio - ls_history[0]) / ls_history[0]) * 100 if ls_history[0] else 0
        
        # Liquidations
        liq_data = self._api_get("/liquidation-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": now - 24 * 3600,
            "to": now,
            "convert_to_usd": "true",
        })
        long_liq = short_liq = 0.0
        if liq_data and liq_data[0].get("history"):
            for item in liq_data[0]["history"]:
                long_liq += float(item.get("l", 0))
                short_liq += float(item.get("s", 0))
        
        return {
            "price": current_price,
            "price_24h_change": price_24h_change,
            "oi_usd": oi_usd,
            "funding_rate": funding_rate,
            "pred_funding": pred_funding,
            "ls_ratio": ls_ratio,
            "ls_24h_change": ls_24h_change,
            "long_liq": long_liq,
            "short_liq": short_liq,
        }
    
    def _api_get(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """API call wrapper."""
        url = f"{self.COINALYZE_BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None
    
    def analyze_with_sonar(self, data: Dict[str, Any]) -> str:
        """Get concise spot trading analysis from Sonar."""
        
        client = OpenAI(
            api_key=self.openai_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        prompt = (
            f"SPOT TRADER ANALYSIS - SOL/USDT\n\n"
            f"DERIVATIVES DATA:\n"
            f"• Price: ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h)\n"
            f"• OI: ${data['oi_usd']/1e6:.1f}M\n"
            f"• Funding: {data['funding_rate']:.3f}% → {data['pred_funding']:.3f}%\n"
            f"• L/S: {data['ls_ratio']:.2f} ({data['ls_24h_change']:+.1f}%)\n"
            f"• Liquidations: ${data['short_liq']/1e6:.1f}M shorts vs ${data['long_liq']/1e6:.1f}M longs\n\n"
            
            "TASK: Quick SOL spot trading analysis\n\n"
            "1. Check SOL charts for current position relative to key levels\n"
            "2. Look for fresh SOL news in last hour only\n"
            "3. Correlate derivatives with price action\n\n"
            
            "RESPONSE FORMAT:\n"
            "🚨 SIGNAL: [LONG|SHORT|WAIT]\n"
            "📊 SETUP: [Brief technical + derivatives correlation]\n"
            "📰 NEWS: [Recent news or 'None']\n"
            "🎯 ENTRY: [Entry zone - be specific]\n"
            "⛔ STOP: [Stop loss level]\n"
            "🎪 TARGET: [2-5% target]\n"
            "⚠️ RISK: [Key risk factor]"
        )
        
        system_prompt = (
            "You are a spot trader focused on quick 2-5% gains. "
            "Keep analysis concise and actionable. "
            "Use derivatives data to confirm technical setups. "
            "Only include news from last hour. "
            "Be specific with entry/exit levels."
        )
        
        try:
            response = client.chat.completions.create(
                model="perplexity/sonar-reasoning-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/sol-spot-trader",
                    "X-Title": "SOL Spot Trader Analysis",
                }
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as exc:
            return f"❌ Analysis failed: {exc}"
    
    def run_analysis(self):
        """Run complete spot trader analysis."""
        print("🎯 SOL Spot Trader Analysis")
        print("📊 Getting derivatives data...")
        
        data = self.get_derivatives_data()
        
        print(f"💰 Price: ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h)")
        print(f"🏦 OI: ${data['oi_usd']/1e6:.1f}M")
        print(f"💸 Funding: {data['funding_rate']:.3f}% → {data['pred_funding']:.3f}%")
        print(f"⚖️ L/S: {data['ls_ratio']:.2f} ({data['ls_24h_change']:+.1f}%)")
        
        print("\n🧠 Getting Sonar analysis...")
        analysis = self.analyze_with_sonar(data)
        
        utc_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        result = (
            f"🎯 SOL SPOT TRADER • {utc_time}\n"
            f"📊 ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h)\n"
            f"{'='*40}\n\n"
            f"{analysis}\n\n"
            f"{'='*40}\n"
            f"🎯 Focus: 2-5% spot gains"
        )
        
        print("\n📋 ANALYSIS RESULT:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        return result

def main():
    """Run spot trader analysis."""
    try:
        trader = SOLSpotTrader()
        trader.run_analysis()
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
