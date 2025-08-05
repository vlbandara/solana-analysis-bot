#!/usr/bin/env python3
"""
Single O3 Solana Analysis Agent
===============================
Clean, single o3 call with ALL data fed at once.
No messy fallbacks, no multiple calls - just pure o3 intelligence.
"""

import os
import time
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from openai import OpenAI
import numpy as np

class SingleO3SolanaAgent:
    def __init__(self):
        self.coinalyze_api_key = os.getenv('COINALYZE_API_KEY')
        if not self.coinalyze_api_key:
            raise ValueError("COINALYZE_API_KEY required")
        
        self.base_url = "https://api.coinalyze.net/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'api_key': self.coinalyze_api_key,
            'User-Agent': 'SingleO3SolanaAgent/1.0'
        })
        
        # SOL symbols
        self.perp_symbol = "SOLUSDT_PERP.A"
        self.spot_symbol = "SOLUSDT.C"
    
    def _safe_get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Safe API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ API {response.status_code} for {endpoint}")
                return None
        except Exception as e:
            print(f"❌ API error for {endpoint}: {e}")
            return None
    
    def fetch_comprehensive_data(self) -> Dict[str, Any]:
        """Fetch ALL data needed for comprehensive o3 analysis"""
        print("🔍 Fetching comprehensive SOL derivatives data...")
        
        current_time = int(time.time())
        data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symbol': 'SOL',
            'data_quality': 'complete'
        }
        
        # 1. Current Price & OHLCV
        print("   💰 Current prices...")
        price_data = self._safe_get("/ohlcv-history", {
            "symbols": self.perp_symbol,
            "interval": "1min",
            "from": current_time - 300,
            "to": current_time
        })
        
        if price_data and price_data[0].get('history'):
            latest = price_data[0]['history'][-1]
            data['current_price'] = float(latest['c'])
            data['current_volume'] = float(latest['v'])
            print(f"      ✅ Price: ${data['current_price']:.2f}")
        else:
            data['current_price'] = 0
            data['current_volume'] = 0
            data['data_quality'] = 'partial'
        
        # 2. Open Interest (current + history)
        print("   🏦 Open Interest...")
        # Current OI
        current_oi = self._safe_get("/open-interest", {
            "symbols": self.perp_symbol,
            "convert_to_usd": "true"
        })
        
        if current_oi:
            data['open_interest_usd'] = float(current_oi[0]['value'])
            print(f"      ✅ OI: ${data['open_interest_usd']/1e6:.1f}M")
        else:
            data['open_interest_usd'] = 0
        
        # OI History (24h)
        oi_history = self._safe_get("/open-interest-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": current_time - (24 * 3600),
            "to": current_time,
            "convert_to_usd": "true"
        })
        
        if oi_history and oi_history[0].get('history'):
            oi_values = [float(h.get('c', h.get('value', 0))) for h in oi_history[0]['history']]
            data['oi_history_24h'] = oi_values
            if len(oi_values) >= 2:
                data['oi_change_24h_pct'] = ((oi_values[-1] - oi_values[0]) / oi_values[0]) * 100
                data['oi_change_1h_pct'] = ((oi_values[-1] - oi_values[-2]) / oi_values[-2]) * 100 if len(oi_values) >= 2 else 0
            else:
                data['oi_change_24h_pct'] = 0
                data['oi_change_1h_pct'] = 0
        else:
            data['oi_history_24h'] = []
            data['oi_change_24h_pct'] = 0
            data['oi_change_1h_pct'] = 0
        
        # 3. Funding Rates
        print("   💸 Funding rates...")
        current_funding = self._safe_get("/funding-rate", {"symbols": self.perp_symbol})
        predicted_funding = self._safe_get("/predicted-funding-rate", {"symbols": self.perp_symbol})
        
        if current_funding:
            data['funding_rate'] = float(current_funding[0]['value'])
            data['funding_rate_pct'] = data['funding_rate'] * 100
            data['funding_rate_annual_pct'] = data['funding_rate'] * 365 * 3 * 100
            print(f"      ✅ Funding: {data['funding_rate_pct']:.4f}%")
        else:
            data['funding_rate'] = 0
            data['funding_rate_pct'] = 0
            data['funding_rate_annual_pct'] = 0
        
        if predicted_funding:
            data['predicted_funding_rate'] = float(predicted_funding[0]['value'])
            data['predicted_funding_rate_pct'] = data['predicted_funding_rate'] * 100
        else:
            data['predicted_funding_rate'] = 0
            data['predicted_funding_rate_pct'] = 0
        
        # 4. Long/Short Ratios (current + history)
        print("   ⚖️ Long/Short ratios...")
        ls_history = self._safe_get("/long-short-ratio-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": current_time - (24 * 3600),
            "to": current_time
        })
        
        if ls_history and ls_history[0].get('history'):
            ls_values = [float(h.get('r', 0)) for h in ls_history[0]['history'] if h.get('r')]
            data['ls_ratio_history'] = ls_values
            if ls_values:
                data['current_ls_ratio'] = ls_values[-1]
                data['avg_ls_ratio_24h'] = sum(ls_values) / len(ls_values)
                data['ls_ratio_change_24h_pct'] = ((ls_values[-1] - ls_values[0]) / ls_values[0]) * 100 if len(ls_values) >= 2 else 0
                data['ls_ratio_change_1h_pct'] = ((ls_values[-1] - ls_values[-2]) / ls_values[-2]) * 100 if len(ls_values) >= 2 else 0
                print(f"      ✅ L/S: {data['current_ls_ratio']:.2f}")
            else:
                data['current_ls_ratio'] = 0
                data['avg_ls_ratio_24h'] = 0
                data['ls_ratio_change_24h_pct'] = 0
                data['ls_ratio_change_1h_pct'] = 0
        else:
            data['ls_ratio_history'] = []
            data['current_ls_ratio'] = 0
            data['avg_ls_ratio_24h'] = 0
            data['ls_ratio_change_24h_pct'] = 0
            data['ls_ratio_change_1h_pct'] = 0
        
        # 5. Liquidations (24h)
        print("   🔥 Liquidations...")
        liq_data = self._safe_get("/liquidation-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": current_time - (24 * 3600),
            "to": current_time,
            "convert_to_usd": "true"
        })
        
        if liq_data and liq_data[0].get('history'):
            liq_history = liq_data[0]['history']
            long_liq_24h = sum(h.get('l', 0) for h in liq_history)
            short_liq_24h = sum(h.get('s', 0) for h in liq_history)
            
            data['long_liquidations_24h_usd'] = long_liq_24h
            data['short_liquidations_24h_usd'] = short_liq_24h
            data['total_liquidations_24h_usd'] = long_liq_24h + short_liq_24h
            data['liquidation_ratio'] = long_liq_24h / max(short_liq_24h, 1)
            print(f"      ✅ Liq 24h: ${long_liq_24h/1e6:.1f}ML / ${short_liq_24h/1e6:.1f}MS")
        else:
            data['long_liquidations_24h_usd'] = 0
            data['short_liquidations_24h_usd'] = 0
            data['total_liquidations_24h_usd'] = 0
            data['liquidation_ratio'] = 1
        
        # 6. Price History (24h for context)
        print("   📈 Price history...")
        price_history = self._safe_get("/ohlcv-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": current_time - (24 * 3600),
            "to": current_time
        })
        
        if price_history and price_history[0].get('history'):
            price_candles = price_history[0]['history']
            closes = [float(c['c']) for c in price_candles]
            highs = [float(c['h']) for c in price_candles]
            lows = [float(c['l']) for c in price_candles]
            volumes = [float(c['v']) for c in price_candles]
            
            data['price_history_24h'] = closes
            data['high_24h'] = max(highs)
            data['low_24h'] = min(lows)
            data['volume_24h'] = sum(volumes)
            
            if len(closes) >= 2:
                data['price_change_24h_pct'] = ((closes[-1] - closes[0]) / closes[0]) * 100
                data['price_change_1h_pct'] = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            else:
                data['price_change_24h_pct'] = 0
                data['price_change_1h_pct'] = 0
                
            print(f"      ✅ 24h: {data['price_change_24h_pct']:+.2f}%")
        else:
            data['price_history_24h'] = []
            data['high_24h'] = data['current_price']
            data['low_24h'] = data['current_price']
            data['volume_24h'] = 0
            data['price_change_24h_pct'] = 0
            data['price_change_1h_pct'] = 0
        
        # 7. Calculate patterns and trends
        data['patterns'] = self._calculate_patterns(data)
        
        print(f"✅ Comprehensive data fetch complete! Quality: {data['data_quality']}")
        return data
    
    def _calculate_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate pattern insights from historical data"""
        patterns = {}
        
        # L/S Ratio patterns
        if data['ls_ratio_history'] and len(data['ls_ratio_history']) >= 12:
            ls_values = data['ls_ratio_history']
            current = ls_values[-1]
            recent_6h = ls_values[-6:]
            earlier_6h = ls_values[-12:-6]
            
            recent_avg = sum(recent_6h) / len(recent_6h)
            earlier_avg = sum(earlier_6h) / len(earlier_6h)
            momentum_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            patterns['ls_ratio'] = {
                'current': current,
                'recent_6h_avg': recent_avg,
                'earlier_6h_avg': earlier_avg,
                'momentum_change_pct': momentum_change,
                'trend': 'increasing' if momentum_change > 3 else 'decreasing' if momentum_change < -3 else 'stable',
                'volatility': float(np.std(ls_values[-12:]))
            }
        
        # OI patterns
        if data['oi_history_24h'] and len(data['oi_history_24h']) >= 12:
            oi_values = data['oi_history_24h']
            recent_6h = oi_values[-6:]
            earlier_6h = oi_values[-12:-6]
            
            recent_avg = sum(recent_6h) / len(recent_6h)
            earlier_avg = sum(earlier_6h) / len(earlier_6h)
            momentum_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            patterns['open_interest'] = {
                'momentum_change_pct': momentum_change,
                'trend': 'increasing' if momentum_change > 2 else 'decreasing' if momentum_change < -2 else 'stable',
                'volatility': float(np.std(oi_values[-12:]))
            }
        
        # Price patterns
        if data['price_history_24h'] and len(data['price_history_24h']) >= 12:
            price_values = data['price_history_24h']
            recent_6h = price_values[-6:]
            earlier_6h = price_values[-12:-6]
            
            recent_avg = sum(recent_6h) / len(recent_6h)
            earlier_avg = sum(earlier_6h) / len(earlier_6h)
            momentum_change = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            patterns['price'] = {
                'momentum_change_pct': momentum_change,
                'trend': 'increasing' if momentum_change > 1 else 'decreasing' if momentum_change < -1 else 'stable'
            }
        
        return patterns
    
    def analyze_with_o3(self, data: Dict[str, Any]) -> str:
        """Single comprehensive o3 analysis with ALL data"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Build comprehensive data summary
        patterns = data.get('patterns', {})
        
        prompt = f"""
        🎯 COMPREHENSIVE SOL DERIVATIVES ANALYSIS • {datetime.now(timezone.utc).strftime('%H:%M UTC')}
        
        You are receiving ALL available market data for a complete analysis. Use your superior o3 reasoning.
        
        ═══════════════════════════════════════════════════════════════════════════════
        📊 COMPLETE MARKET DATA SNAPSHOT
        ═══════════════════════════════════════════════════════════════════════════════
        
        💰 CURRENT PRICE DATA:
        • Price: ${data.get('current_price', 0):.2f}
        • 24h Change: {data.get('price_change_24h_pct', 0):+.2f}%
        • 1h Change: {data.get('price_change_1h_pct', 0):+.2f}%
        • 24h Range: ${data.get('low_24h', 0):.2f} - ${data.get('high_24h', 0):.2f}
        • 24h Volume: {data.get('volume_24h', 0):,.0f}
        
        🏦 OPEN INTEREST ANALYSIS:
        • Current OI: ${data.get('open_interest_usd', 0):,.0f} (${data.get('open_interest_usd', 0)/1e6:.1f}M)
        • OI Change 24h: {data.get('oi_change_24h_pct', 0):+.2f}%
        • OI Change 1h: {data.get('oi_change_1h_pct', 0):+.2f}%
        • OI Pattern: {patterns.get('open_interest', {}).get('trend', 'unknown')} trend, {patterns.get('open_interest', {}).get('momentum_change_pct', 0):+.1f}% momentum
        
        💸 FUNDING DYNAMICS:
        • Current Rate: {data.get('funding_rate_pct', 0):.4f}% (Annual: {data.get('funding_rate_annual_pct', 0):+.1f}%)
        • Predicted Rate: {data.get('predicted_funding_rate_pct', 0):.4f}%
        • Interpretation: {'Longs paying shorts' if data.get('funding_rate', 0) > 0 else 'Shorts paying longs' if data.get('funding_rate', 0) < 0 else 'Neutral'}
        
        ⚖️ POSITIONING INTELLIGENCE:
        • Current L/S Ratio: {data.get('current_ls_ratio', 0):.2f}
        • 24h Average L/S: {data.get('avg_ls_ratio_24h', 0):.2f}
        • L/S Change 24h: {data.get('ls_ratio_change_24h_pct', 0):+.2f}%
        • L/S Change 1h: {data.get('ls_ratio_change_1h_pct', 0):+.2f}%
        • L/S Pattern: {patterns.get('ls_ratio', {}).get('trend', 'unknown')} trend, volatility {patterns.get('ls_ratio', {}).get('volatility', 0):.2f}
        
        🔥 LIQUIDATION DATA (24h):
        • Long Liquidations: ${data.get('long_liquidations_24h_usd', 0):,.0f} (${data.get('long_liquidations_24h_usd', 0)/1e6:.2f}M)
        • Short Liquidations: ${data.get('short_liquidations_24h_usd', 0):,.0f} (${data.get('short_liquidations_24h_usd', 0)/1e6:.2f}M)
        • Total Liquidations: ${data.get('total_liquidations_24h_usd', 0):,.0f} (${data.get('total_liquidations_24h_usd', 0)/1e6:.2f}M)
        • Liquidation Ratio: {data.get('liquidation_ratio', 0):.2f} (Long/Short)
        
        📈 PATTERN INSIGHTS:
        • Price Momentum: {patterns.get('price', {}).get('trend', 'unknown')} ({patterns.get('price', {}).get('momentum_change_pct', 0):+.1f}% change)
        • L/S Positioning: Current {data.get('current_ls_ratio', 0):.2f} vs Recent 6h avg {patterns.get('ls_ratio', {}).get('recent_6h_avg', 0):.2f}
        • OI Flow: {patterns.get('open_interest', {}).get('trend', 'unknown')} with {patterns.get('open_interest', {}).get('momentum_change_pct', 0):+.1f}% momentum
        
        ═══════════════════════════════════════════════════════════════════════════════
        🧠 O3 ANALYSIS REQUIREMENTS
        ═══════════════════════════════════════════════════════════════════════════════
        
        Use your superior reasoning to analyze ALL this data comprehensively. Provide:
        
        🎯 BIAS: BULLISH / BEARISH / NEUTRAL / UNCLEAR
        - Only choose BULLISH/BEARISH if evidence strongly supports it
        - Use UNCLEAR if patterns conflict or data is insufficient
        
        📊 KEY INSIGHT: What is the MOST significant pattern or change in this data? 
        - Focus on relationships between metrics (OI vs L/S, funding vs positioning, etc.)
        - Explain what this reveals about institutional vs retail behavior
        - Identify any divergences or unusual patterns
        
        ⚠️ TOP RISK: Based on current positioning and patterns, what's the highest probability risk scenario?
        - Consider liquidation cascades, funding squeezes, positioning reversals
        - Provide specific price levels where risks materialize
        
        💡 ACTION: Specific, actionable recommendation with:
        - Entry strategy and price levels
        - Risk management (stop loss, position sizing)
        - Time horizon and key levels to monitor
        
        CRITICAL INSTRUCTIONS:
        • Analyze the RELATIONSHIPS between metrics, not just individual values
        • Focus on what has CHANGED and what it means for market dynamics
        • Consider both immediate (1h) and broader (24h) patterns
        • Be specific with price levels and risk management
        • If evidence conflicts, clearly state UNCLEAR bias and explain why
        
        This is professional derivatives analysis - be precise, insightful, and actionable.
        """
        
        try:
            print("🧠 Engaging o3 model for comprehensive single-call analysis...")
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an elite institutional derivatives trader and quantitative analyst with 25+ years of experience. You excel at synthesizing complex market data into actionable insights. You specialize in pattern recognition, market microstructure, positioning analysis, and risk assessment. Use your superior reasoning capabilities to provide institutional-grade analysis that identifies subtle market dynamics and regime changes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ O3 analysis failed: {e}"
    
    def format_for_whatsapp(self, analysis: str, data: Dict[str, Any]) -> str:
        """Format analysis for WhatsApp delivery"""
        header = f"🎯 SOL DERIVATIVES • {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n"
        header += f"📊 ${data.get('current_price', 0):.2f} | OI: ${data.get('open_interest_usd', 0)/1e6:.1f}M ({data.get('oi_change_24h_pct', 0):+.1f}% 24h)\n"
        header += f"💸 Funding: {data.get('funding_rate_pct', 0):.4f}% | L/S: {data.get('current_ls_ratio', 0):.2f}\n\n"
        
        footer = "\n\n📈 Coinalyze + o3"
        
        return header + analysis + footer


def run_single_o3_analysis():
    """Main function for single o3 comprehensive analysis"""
    print("🚀 Starting Single O3 SOL Analysis...")
    print("=" * 80)
    
    try:
        agent = SingleO3SolanaAgent()
        
        # Fetch ALL data
        data = agent.fetch_comprehensive_data()
        
        if data['data_quality'] == 'complete':
            print("✅ Complete data available for o3 analysis")
        else:
            print("⚠️ Partial data - proceeding with available information")
        
        # Single o3 analysis with all data
        analysis = agent.analyze_with_o3(data)
        
        print("\n" + "="*80)
        print("🧠 SINGLE O3 COMPREHENSIVE ANALYSIS")
        print("="*80)
        print(analysis)
        print("\n" + "="*80)
        
        # Format for WhatsApp
        whatsapp_format = agent.format_for_whatsapp(analysis, data)
        
        print("\n📱 WHATSAPP FORMAT:")
        print("-" * 50)
        print(whatsapp_format)
        print("-" * 50)
        
        # Save results
        results = {
            'analysis': analysis,
            'whatsapp_format': whatsapp_format,
            'raw_data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model': 'o3_single_call',
            'data_quality': data['data_quality']
        }
        
        with open('single_o3_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n💾 Results saved to single_o3_analysis.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Single o3 analysis failed: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Single O3 SOL derivatives analysis")
    parser.add_argument("--whatsapp", action="store_true", help="Send to WhatsApp")
    args = parser.parse_args()
    
    result = run_single_o3_analysis()
    
    if result and args.whatsapp:
        try:
            from whatsapp_sender import WhatsAppSender
            sender = WhatsAppSender()
            sender.send_message(result['whatsapp_format'])
            print("✅ Sent to WhatsApp!")
        except Exception as e:
            print(f"❌ WhatsApp send failed: {e}")
    
    if result:
        print("\n✅ Single o3 analysis complete!")
        print("🎯 Clean, comprehensive analysis with all data in single call")
    else:
        print("\n❌ Analysis failed!")