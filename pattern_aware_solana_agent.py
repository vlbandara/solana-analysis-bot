#!/usr/bin/env python3
"""
Pattern-Aware Solana Analysis Agent
===================================
Enhanced crypto analysis that focuses on PATTERNS and TRENDS instead of just snapshots.
Analyzes how metrics have changed over recent hours/days to provide contextual insights.

Key Features:
- Historical pattern detection (1h, 4h, 24h comparisons)
- Trend analysis for L/S ratios, funding rates, open interest
- Significant change detection and alerts
- Context-aware AI prompts that understand market momentum
"""

import os
import time
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from openai import OpenAI
import numpy as np

@dataclass
class MetricPattern:
    """Represents a pattern/trend for a specific metric"""
    current_value: float
    value_1h_ago: Optional[float]
    value_4h_ago: Optional[float]
    value_24h_ago: Optional[float]
    change_1h: Optional[float]
    change_4h: Optional[float]
    change_24h: Optional[float]
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    volatility: float
    significance: str  # 'high', 'medium', 'low'
    
    def get_change_description(self, timeframe: str) -> str:
        """Get human-readable description of change"""
        change_map = {'1h': self.change_1h, '4h': self.change_4h, '24h': self.change_24h}
        value_map = {'1h': self.value_1h_ago, '4h': self.value_4h_ago, '24h': self.value_24h_ago}
        
        change = change_map.get(timeframe)
        old_value = value_map.get(timeframe)
        
        if change is None or old_value is None:
            return f"No {timeframe} data"
        
        direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        return f"{direction} {change:+.2f}% from {old_value:.2f} ({timeframe} ago)"

class PatternAwareSolanaAgent:
    def __init__(self):
        self.coinalyze_api_key = os.getenv('COINALYZE_API_KEY')
        if not self.coinalyze_api_key:
            raise ValueError("COINALYZE_API_KEY required")
        
        self.base_url = "https://api.coinalyze.net/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'api_key': self.coinalyze_api_key,
            'User-Agent': 'PatternAwareSolanaAgent/1.0'
        })
        
        # SOL symbols
        self.perp_symbol = "SOLUSDT_PERP.A"
        self.spot_symbol = "SOLUSDT.C"
    
    def _coinalyze_get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make API request to Coinalyze"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API error for {endpoint}: {e}")
            return None
    
    def fetch_historical_series(self, endpoint: str, symbol: str, hours: int = 24, interval: str = "1hour") -> List[Dict]:
        """Fetch historical time series data"""
        to_ts = int(time.time())
        from_ts = to_ts - (hours * 3600)
        
        params = {
            "symbols": symbol,
            "interval": interval,
            "from": from_ts,
            "to": to_ts
        }
        
        if "open-interest" in endpoint:
            params["convert_to_usd"] = "true"
        elif "liquidation" in endpoint:
            params["convert_to_usd"] = "true"
        
        data = self._coinalyze_get(endpoint, params)
        if data and len(data) > 0 and 'history' in data[0]:
            return data[0]['history']
        return []
    
    def extract_values_from_history(self, history: List[Dict], value_key: str = 'c') -> List[Tuple[int, float]]:
        """Extract timestamp and values from history data"""
        values = []
        for item in history:
            # Try different keys in order of preference
            value = None
            for key in [value_key, 'c', 'value', 'v', 'r']:
                if key in item and item[key] is not None:
                    value = float(item[key])
                    break
            
            if value is not None:
                ts = item.get('t', item.get('timestamp', 0))
                values.append((int(ts), value))
        
        return sorted(values, key=lambda x: x[0])  # Sort by timestamp
    
    def calculate_pattern(self, values: List[Tuple[int, float]], metric_name: str) -> MetricPattern:
        """Calculate pattern analysis for a metric"""
        if not values:
            return MetricPattern(0, None, None, None, None, None, None, 'stable', 0, 'low')
        
        # Current and historical values
        current_ts, current_value = values[-1]
        
        # Find values at specific time intervals
        now = int(time.time())
        value_1h_ago = self._find_closest_value(values, now - 3600)
        value_4h_ago = self._find_closest_value(values, now - 14400)
        value_24h_ago = self._find_closest_value(values, now - 86400)
        
        # Calculate percentage changes
        change_1h = ((current_value - value_1h_ago) / value_1h_ago * 100) if value_1h_ago else None
        change_4h = ((current_value - value_4h_ago) / value_4h_ago * 100) if value_4h_ago else None
        change_24h = ((current_value - value_24h_ago) / value_24h_ago * 100) if value_24h_ago else None
        
        # Determine trend direction
        trend_direction = self._determine_trend(values)
        
        # Calculate volatility (standard deviation of recent values)
        recent_values = [v[1] for v in values[-12:]]  # Last 12 hours
        volatility = float(np.std(recent_values)) if len(recent_values) > 1 else 0
        
        # Determine significance based on change magnitude
        significance = self._determine_significance(change_1h, change_4h, change_24h, metric_name)
        
        return MetricPattern(
            current_value=current_value,
            value_1h_ago=value_1h_ago,
            value_4h_ago=value_4h_ago,
            value_24h_ago=value_24h_ago,
            change_1h=change_1h,
            change_4h=change_4h,
            change_24h=change_24h,
            trend_direction=trend_direction,
            volatility=volatility,
            significance=significance
        )
    
    def _find_closest_value(self, values: List[Tuple[int, float]], target_ts: int) -> Optional[float]:
        """Find the value closest to target timestamp"""
        if not values:
            return None
        
        # Find the closest timestamp
        closest = min(values, key=lambda x: abs(x[0] - target_ts))
        
        # Only return if within reasonable time window (2 hours)
        if abs(closest[0] - target_ts) <= 7200:
            return closest[1]
        return None
    
    def _determine_trend(self, values: List[Tuple[int, float]]) -> str:
        """Determine overall trend direction"""
        if len(values) < 3:
            return 'stable'
        
        recent_values = [v[1] for v in values[-6:]]  # Last 6 hours
        
        # Simple linear trend
        x = list(range(len(recent_values)))
        correlation = np.corrcoef(x, recent_values)[0, 1] if len(recent_values) > 1 else 0
        
        if correlation > 0.3:
            return 'increasing'
        elif correlation < -0.3:
            return 'decreasing'
        else:
            return 'stable'
    
    def _determine_significance(self, change_1h: Optional[float], change_4h: Optional[float], change_24h: Optional[float], metric_name: str) -> str:
        """Determine if changes are significant based on metric type"""
        # Different thresholds for different metrics
        thresholds = {
            'long_short_ratio': {'high': 15, 'medium': 5},  # L/S ratio changes
            'funding_rate': {'high': 50, 'medium': 20},     # Funding rate changes
            'open_interest': {'high': 10, 'medium': 3},     # OI changes
            'price': {'high': 5, 'medium': 2}               # Price changes
        }
        
        threshold = thresholds.get(metric_name, {'high': 10, 'medium': 3})
        
        # Check the most recent significant change
        for change in [change_1h, change_4h, change_24h]:
            if change is not None:
                abs_change = abs(change)
                if abs_change >= threshold['high']:
                    return 'high'
                elif abs_change >= threshold['medium']:
                    return 'medium'
        
        return 'low'
    
    def fetch_all_patterns(self) -> Dict[str, Any]:
        """Fetch all metrics with pattern analysis"""
        print("🔍 Fetching comprehensive pattern data...")
        
        # Fetch current values first
        current_data = self._fetch_current_snapshot()
        
        # Fetch historical data for pattern analysis
        patterns = {}
        
        # 1. Long/Short Ratio Pattern
        print("   📊 Analyzing L/S ratio patterns...")
        ls_history = self.fetch_historical_series("/long-short-ratio-history", self.perp_symbol, 48)
        ls_values = self.extract_values_from_history(ls_history, 'r')
        patterns['long_short_ratio'] = self.calculate_pattern(ls_values, 'long_short_ratio')
        
        # 2. Funding Rate Pattern
        print("   💸 Analyzing funding rate patterns...")
        fr_history = self.fetch_historical_series("/funding-rate-history", self.perp_symbol, 48, "8hour")
        fr_values = self.extract_values_from_history(fr_history, 'c')
        patterns['funding_rate'] = self.calculate_pattern(fr_values, 'funding_rate')
        
        # 3. Open Interest Pattern
        print("   🏦 Analyzing open interest patterns...")
        oi_history = self.fetch_historical_series("/open-interest-history", self.perp_symbol, 48)
        oi_values = self.extract_values_from_history(oi_history, 'c')
        patterns['open_interest'] = self.calculate_pattern(oi_values, 'open_interest')
        
        # 4. Liquidations Pattern (combine long + short)
        print("   ⚡ Analyzing liquidation patterns...")
        liq_history = self.fetch_historical_series("/liquidation-history", self.perp_symbol, 48)
        liq_values = []
        for item in liq_history:
            ts = item.get('t', item.get('timestamp', 0))
            long_liq = item.get('l', 0)
            short_liq = item.get('s', 0)
            total_liq = long_liq + short_liq
            if total_liq > 0:
                liq_values.append((int(ts), total_liq))
        patterns['liquidations'] = self.calculate_pattern(liq_values, 'liquidations')
        
        # 5. Price Pattern (for context)
        print("   💰 Analyzing price patterns...")
        price_history = self.fetch_historical_series("/ohlcv-history", self.perp_symbol, 48)
        price_values = self.extract_values_from_history(price_history, 'c')
        patterns['price'] = self.calculate_pattern(price_values, 'price')
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'current_data': current_data,
            'patterns': patterns,
            'analysis_type': 'pattern_aware'
        }
    
    def _fetch_current_snapshot(self) -> Dict[str, Any]:
        """Fetch current snapshot data"""
        current = {}
        
        # Current price
        try:
            price_data = self._coinalyze_get("/ohlcv-history", {
                "symbols": self.perp_symbol,
                "interval": "1min",
                "from": int(time.time()) - 300,
                "to": int(time.time())
            })
            if price_data and price_data[0].get('history'):
                current['price'] = float(price_data[0]['history'][-1]['c'])
        except:
            current['price'] = 0
        
        # Current OI
        try:
            oi_data = self._coinalyze_get("/open-interest", {
                "symbols": self.perp_symbol,
                "convert_to_usd": "true"
            })
            if oi_data:
                current['open_interest_usd'] = float(oi_data[0]['value'])
        except:
            current['open_interest_usd'] = 0
        
        return current
    
    def generate_pattern_analysis(self, data: Dict[str, Any]) -> str:
        """Generate AI analysis focused on patterns and trends"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        patterns = data['patterns']
        current = data['current_data']
        
        # Build comprehensive pattern context for AI
        pattern_context = self._build_pattern_context(patterns, current)
        
        prompt = f"""
        🎯 SOL DERIVATIVES PATTERN ANALYSIS • {datetime.now(timezone.utc).strftime('%H:%M UTC')}
        
        📊 CURRENT SNAPSHOT:
        💰 Price: ${current.get('price', 0):.2f}
        🏦 Open Interest: ${current.get('open_interest_usd', 0)/1e6:.1f}M
        
        🔍 PATTERN ANALYSIS - Focus on TRENDS and CHANGES:
        
        {pattern_context}
        
        ═══════════════════════════════════════════════════════════════════════════════
        📋 ANALYSIS REQUIREMENTS:
        
        You are an expert derivatives trader analyzing SOL patterns. Provide:
        
        1. 🎯 BIAS: BULLISH/BEARISH/NEUTRAL (based on pattern convergence)
        
        2. 📊 KEY INSIGHT: Focus on the MOST SIGNIFICANT pattern change. What does the biggest shift tell us about market sentiment and positioning?
        
        3. ⚠️ TOP RISK: Identify the highest probability risk based on current patterns (e.g., liquidation cascade, funding squeeze, positioning reversal)
        
        4. 💡 ACTION: Specific actionable recommendation based on pattern analysis
        
        CRITICAL: 
        - Focus on PATTERNS and CHANGES, not just current values
        - Highlight the most significant shifts in the data
        - Explain what these patterns indicate about trader behavior
        - Keep it concise but insightful - suitable for quick trading decisions
        
        Format as:
        🎯 BIAS: [DIRECTION]
        📊 KEY INSIGHT: [Most important pattern observation]
        ⚠️ TOP RISK: [Highest probability risk scenario]  
        💡 ACTION: [Specific recommendation]
        """
        
        try:
            # Use full o3 model for superior pattern recognition
            print("🧠 Engaging o3 model for advanced pattern analysis...")
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an elite cryptocurrency derivatives trader with 20+ years of experience. You specialize in advanced pattern recognition, market microstructure analysis, and derivatives trading. You excel at identifying subtle market dynamics, trend reversals, and positioning shifts that other traders miss. Use your superior reasoning capabilities to provide deep insights into what the patterns reveal about institutional vs retail behavior, liquidation risks, and market sentiment shifts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=1500  # More tokens for deeper o3 analysis
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"⚠️ o3 model error: {e}")
            # Fallback to o3-mini if o3 fails, then GPT-4
            try:
                print("🔄 Falling back to o3-mini...")
                response = client.chat.completions.create(
                    model="o3-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert derivatives trader specializing in pattern analysis."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=800
                )
                return response.choices[0].message.content
            except Exception as fallback_e:
                print(f"🔄 Final fallback to GPT-4...")
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert derivatives trader. Analyze patterns and trends."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=600,
                        temperature=0.1
                    )
                    return response.choices[0].message.content
                except Exception as final_e:
                    return f"Analysis unavailable. o3 error: {e}, o3-mini error: {fallback_e}, GPT-4 error: {final_e}"
    
    def _build_pattern_context(self, patterns: Dict[str, MetricPattern], current: Dict[str, Any]) -> str:
        """Build detailed pattern context for AI analysis"""
        context_parts = []
        
        # L/S Ratio Analysis
        ls_pattern = patterns.get('long_short_ratio')
        if ls_pattern:
            context_parts.append(
                f"📊 LONG/SHORT RATIO: {ls_pattern.current_value:.2f}\n"
                f"   • {ls_pattern.get_change_description('1h')}\n"
                f"   • {ls_pattern.get_change_description('4h')}\n"
                f"   • {ls_pattern.get_change_description('24h')}\n"
                f"   • Trend: {ls_pattern.trend_direction} | Significance: {ls_pattern.significance}"
            )
        
        # Funding Rate Analysis  
        fr_pattern = patterns.get('funding_rate')
        if fr_pattern:
            context_parts.append(
                f"💸 FUNDING RATE: {fr_pattern.current_value*100:.4f}%\n"
                f"   • {fr_pattern.get_change_description('4h')}\n"
                f"   • {fr_pattern.get_change_description('24h')}\n"
                f"   • Trend: {fr_pattern.trend_direction} | Significance: {fr_pattern.significance}"
            )
        
        # Open Interest Analysis
        oi_pattern = patterns.get('open_interest')
        if oi_pattern:
            context_parts.append(
                f"🏦 OPEN INTEREST: ${oi_pattern.current_value/1e6:.1f}M\n"
                f"   • {oi_pattern.get_change_description('1h')}\n"
                f"   • {oi_pattern.get_change_description('4h')}\n"
                f"   • {oi_pattern.get_change_description('24h')}\n"
                f"   • Trend: {oi_pattern.trend_direction} | Significance: {oi_pattern.significance}"
            )
        
        # Liquidations Analysis
        liq_pattern = patterns.get('liquidations')
        if liq_pattern:
            context_parts.append(
                f"⚡ LIQUIDATIONS: ${liq_pattern.current_value/1e6:.2f}M (last hour)\n"
                f"   • {liq_pattern.get_change_description('4h')}\n"
                f"   • Trend: {liq_pattern.trend_direction} | Significance: {liq_pattern.significance}"
            )
        
        # Price Pattern
        price_pattern = patterns.get('price')
        if price_pattern:
            context_parts.append(
                f"💰 PRICE MOMENTUM: ${price_pattern.current_value:.2f}\n"
                f"   • {price_pattern.get_change_description('1h')}\n"
                f"   • {price_pattern.get_change_description('4h')}\n"
                f"   • Trend: {price_pattern.trend_direction}"
            )
        
        return "\n\n".join(context_parts)
    
    def format_whatsapp_analysis(self, analysis: str, data: Dict[str, Any]) -> str:
        """Format analysis for WhatsApp delivery"""
        current = data['current_data']
        patterns = data['patterns']
        
        # Get key metrics for header
        ls_ratio = patterns.get('long_short_ratio', {})
        funding = patterns.get('funding_rate', {})
        oi = patterns.get('open_interest', {})
        
        ls_current = getattr(ls_ratio, 'current_value', 0)
        funding_current = getattr(funding, 'current_value', 0) * 100
        oi_current = getattr(oi, 'current_value', 0) / 1e6
        
        # Get most significant change for header
        oi_change_24h = getattr(oi, 'change_24h', 0)
        oi_change_str = f"${oi_change_24h:+.2f}M 24h" if oi_change_24h else "$0M 24h"
        
        header = f"🎯 SOL DERIVATIVES • {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n\n"
        header += f"📊 ${current.get('price', 0):.2f} | OI: ${oi_current:.1f}B ({oi_change_str})\n"
        header += f"💸 Funding: {funding_current:.4f}% | L/S: {ls_current:.2f}\n\n"
        
        footer = f"\n\n📈 Coinalyze + o3"
        
        return header + analysis + footer


def run_pattern_analysis():
    """Main function for pattern-aware analysis"""
    print("🚀 Starting Pattern-Aware SOL Analysis...")
    print("=" * 80)
    
    try:
        agent = PatternAwareSolanaAgent()
        
        # Fetch all data with pattern analysis
        data = agent.fetch_all_patterns()
        
        if not data or not data.get('patterns'):
            print("❌ Failed to fetch pattern data!")
            return None
        
        print(f"\n📊 Pattern analysis complete!")
        print(f"💰 Current Price: ${data['current_data'].get('price', 0):.2f}")
        
        # Show pattern summary
        patterns = data['patterns']
        for metric_name, pattern in patterns.items():
            if hasattr(pattern, 'significance') and pattern.significance in ['high', 'medium']:
                print(f"🔥 {metric_name.upper()}: {pattern.current_value:.2f} ({pattern.significance} significance)")
        
        # Generate AI analysis
        analysis = agent.generate_pattern_analysis(data)
        
        print("\n" + "="*80)
        print("🧠 PATTERN-AWARE SOL ANALYSIS")
        print("="*80)
        print(analysis)
        print("\n" + "="*80)
        
        # Format for WhatsApp
        whatsapp_format = agent.format_whatsapp_analysis(analysis, data)
        
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
            'analysis_type': 'pattern_aware'
        }
        
        with open('pattern_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n💾 Results saved to pattern_analysis.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pattern-aware SOL derivatives analysis")
    parser.add_argument("--whatsapp", action="store_true", help="Send to WhatsApp")
    args = parser.parse_args()
    
    result = run_pattern_analysis()
    
    if result and args.whatsapp:
        try:
            from whatsapp_sender import WhatsAppSender
            sender = WhatsAppSender()
            sender.send_message(result['whatsapp_format'])
            print("✅ Sent to WhatsApp!")
        except Exception as e:
            print(f"❌ WhatsApp send failed: {e}")
    
    if result:
        print("\n✅ Pattern-aware analysis complete!")
        print("🔍 Analysis focuses on trends and significant changes")
    else:
        print("\n❌ Analysis failed!")