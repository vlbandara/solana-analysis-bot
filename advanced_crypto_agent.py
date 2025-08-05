#!/usr/bin/env python3
"""
Advanced Coinalyze-Only Crypto Analysis Agent
Streamlined intelligent crypto analysis using only Coinalyze API
Based on: https://api.coinalyze.net/v1/doc/
"""

import os
import requests
import time
from datetime import datetime, timezone
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional

class AdvancedCryptoAgent:
    def __init__(self):
        self.coinalyze_api_key = os.getenv('COINALYZE_API_KEY')
        if not self.coinalyze_api_key:
            raise ValueError("COINALYZE_API_KEY required. Get free key from https://coinalyze.net")
        
        self.base_url = "https://api.coinalyze.net/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'api_key': self.coinalyze_api_key,
            'User-Agent': 'AdvancedCoinalyzeAgent/1.0'
        })
    
    def decide_coinalyze_metrics_needed(self, crypto_symbol):
        """AI decides what Coinalyze metrics to fetch for analysis"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        As a crypto derivatives trading agent, determine what Coinalyze API metrics are most important for analyzing {crypto_symbol}.
        
        Available Coinalyze metrics:
        1. current_prices - OHLCV data and current prices
        2. open_interest - Current and historical open interest
        3. funding_rates - Current and predicted funding rates  
        4. liquidations - Recent liquidation data (long/short)
        5. long_short_ratios - Trader positioning data
        6. funding_history - Historical funding rate trends (ESSENTIAL for pattern analysis)
        7. oi_history - Open interest historical trends (ESSENTIAL for pattern analysis)
        
        For PATTERN-AWARE analysis, always include funding_history and oi_history for trend detection.
        Return only a JSON list of the most important 5-6 metrics for pattern-aware derivatives analysis.
        Example: ["current_prices", "open_interest", "funding_rates", "liquidations", "long_short_ratios", "funding_history"]
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            # Parse the AI's decision
            sources_text = response.choices[0].message.content.strip()
            if "[" in sources_text and "]" in sources_text:
                import ast
                return ast.literal_eval(sources_text)
            else:
                # Fallback to essential metrics (including historical for patterns)
                return ["current_prices", "open_interest", "funding_rates", "liquidations", "long_short_ratios", "funding_history", "oi_history"]
                
        except Exception as e:
            print(f"⚠️ AI metric selection failed: {e}")
            return ["current_prices", "open_interest", "funding_rates", "liquidations", "long_short_ratios", "funding_history"]
    
    def fetch_intelligent_data(self, symbol):
        """Fetch data based on AI's decision of what Coinalyze metrics are needed"""
        needed_metrics = self.decide_coinalyze_metrics_needed(symbol)
        print(f"🤖 AI decided to fetch: {', '.join(needed_metrics)}")
        
        # Find symbol mappings
        perp_symbol, spot_symbol = self.find_symbol_mappings(symbol)
        
        data = {}
        
        for metric in needed_metrics:
            if metric == "current_prices":
                data['prices'] = self.fetch_ohlcv_data(perp_symbol)
            elif metric == "open_interest":
                data['open_interest'] = self.fetch_open_interest(perp_symbol)
            elif metric == "funding_rates":
                data['funding'] = self.fetch_funding_rates(perp_symbol)
            elif metric == "liquidations":
                data['liquidations'] = self.fetch_liquidations(perp_symbol)
            elif metric == "long_short_ratios":
                data['positioning'] = self.fetch_long_short_ratios(perp_symbol)
            elif metric == "funding_history":
                data['funding_history'] = self.fetch_funding_history(perp_symbol)
            elif metric == "oi_history":
                data['oi_history'] = self.fetch_oi_history(perp_symbol)
        
        return data
    
    def _coinalyze_get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make API request to Coinalyze"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Invalid COINALYZE_API_KEY")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            else:
                raise ValueError(f"API error {response.status_code}: {e}")
        except Exception as e:
            raise ValueError(f"Request failed: {e}")
    
    def find_symbol_mappings(self, crypto: str) -> tuple[str, str]:
        """Find perpetual and spot symbols for a cryptocurrency"""
        future_markets = self._coinalyze_get("/future-markets")
        spot_markets = self._coinalyze_get("/spot-markets")
        
        crypto_upper = crypto.upper()
        
        # Find perpetual contract
        perp_symbol = None
        for market in future_markets:
            if (market['base_asset'] == crypto_upper and 
                market['is_perpetual'] and 
                market['quote_asset'] in ['USDT', 'USD']):
                perp_symbol = market['symbol']
                if market['quote_asset'] == 'USDT':
                    break
        
        # Find spot market
        spot_symbol = None
        for market in spot_markets:
            if (market['base_asset'] == crypto_upper and 
                market['quote_asset'] in ['USDT', 'USD']):
                spot_symbol = market['symbol']
                if market['quote_asset'] == 'USDT':
                    break
        
        if not perp_symbol:
            raise ValueError(f"No perpetual contract found for {crypto}")
        if not spot_symbol:
            spot_symbol = perp_symbol
            
        return perp_symbol, spot_symbol
    
    def fetch_ohlcv_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch OHLCV data from Coinalyze"""
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (24 * 3600)  # 24 hours
            
            data = self._coinalyze_get("/ohlcv-history", {
                "symbols": symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts
            })
            
            if data and data[0]['history']:
                history = data[0]['history']
                current = history[-1]
                
                # Calculate price changes
                price_24h_ago = history[0]['c'] if len(history) > 0 else current['c']
                price_change_24h = ((current['c'] - price_24h_ago) / price_24h_ago) * 100
                
                return {
                    'current_price': float(current['c']),
                    'high_24h': max(h['h'] for h in history),
                    'low_24h': min(h['l'] for h in history),
                    'volume_24h': sum(h['v'] for h in history),
                    'price_change_24h': price_change_24h,
                    'ohlcv_history': history
                }
        except Exception as e:
            print(f"❌ OHLCV data error: {e}")
            return {}
    
    def fetch_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Fetch open interest data"""
        try:
            # Current OI
            current_oi = self._coinalyze_get("/open-interest", {
                "symbols": symbol,
                "convert_to_usd": "true"
            })
            
            # OI History
            to_ts = int(time.time())
            from_ts = to_ts - (24 * 3600)
            
            oi_history = self._coinalyze_get("/open-interest-history", {
                "symbols": symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts,
                "convert_to_usd": "true"
            })
            
            result = {}
            if current_oi:
                result['current_oi_usd'] = float(current_oi[0]['value'])
            
            if oi_history and oi_history[0]['history']:
                history = oi_history[0]['history']
                result['oi_history'] = [float(h.get('c', h.get('value', 0))) for h in history]
                if len(result['oi_history']) > 1:
                    result['oi_change_24h_pct'] = ((result['oi_history'][-1] - result['oi_history'][0]) / result['oi_history'][0]) * 100
            
            return result
        except Exception as e:
            print(f"❌ Open Interest error: {e}")
            return {}
    
    def fetch_funding_rates(self, symbol: str) -> Dict[str, Any]:
        """Fetch funding rate data"""
        try:
            # Current funding rate
            current_fr = self._coinalyze_get("/funding-rate", {"symbols": symbol})
            
            # Predicted funding rate
            predicted_fr = self._coinalyze_get("/predicted-funding-rate", {"symbols": symbol})
            
            result = {}
            if current_fr:
                result['current_funding_rate'] = float(current_fr[0]['value'])
                result['current_funding_rate_pct'] = result['current_funding_rate'] * 100
            
            if predicted_fr:
                result['predicted_funding_rate'] = float(predicted_fr[0]['value'])
                result['predicted_funding_rate_pct'] = result['predicted_funding_rate'] * 100
            
            return result
        except Exception as e:
            print(f"❌ Funding Rate error: {e}")
            return {}
    
    def fetch_liquidations(self, symbol: str) -> Dict[str, Any]:
        """Fetch liquidation data"""
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (24 * 3600)  # Last 24 hours
            
            liq_data = self._coinalyze_get("/liquidation-history", {
                "symbols": symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts,
                "convert_to_usd": "true"
            })
            
            if liq_data and liq_data[0]['history']:
                history = liq_data[0]['history']
                long_liq = sum(h.get('l', 0) for h in history)
                short_liq = sum(h.get('s', 0) for h in history)
                
                return {
                    'liquidations_long_24h_usd': long_liq,
                    'liquidations_short_24h_usd': short_liq,
                    'liquidation_ratio': long_liq / max(short_liq, 1),
                    'total_liquidations_24h_usd': long_liq + short_liq
                }
        except Exception as e:
            print(f"❌ Liquidations error: {e}")
            return {}
    
    def fetch_long_short_ratios(self, symbol: str) -> Dict[str, Any]:
        """Fetch long/short ratio data"""
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (24 * 3600)
            
            ls_data = self._coinalyze_get("/long-short-ratio-history", {
                "symbols": symbol,
                "interval": "1hour",
                "from": from_ts,
                "to": to_ts
            })
            
            if ls_data and ls_data[0]['history']:
                history = ls_data[0]['history']
                ratios = [h.get('r', 0) for h in history if h.get('r')]
                
                return {
                    'current_ls_ratio': ratios[-1] if ratios else 0,
                    'avg_ls_ratio_24h': sum(ratios) / len(ratios) if ratios else 0,
                    'ls_ratio_history': ratios
                }
        except Exception as e:
            print(f"❌ Long/Short Ratio error: {e}")
            return {}
    
    def fetch_funding_history(self, symbol: str) -> Dict[str, Any]:
        """Fetch funding rate history"""
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (7 * 24 * 3600)  # Last 7 days
            
            fr_history = self._coinalyze_get("/funding-rate-history", {
                "symbols": symbol,
                "interval": "8hour",  # Funding happens every 8 hours
                "from": from_ts,
                "to": to_ts
            })
            
            if fr_history and fr_history[0]['history']:
                history = fr_history[0]['history']
                rates = [h.get('c', h.get('value', 0)) for h in history]
                
                return {
                    'funding_rate_history': rates,
                    'avg_funding_rate_7d': sum(rates) / len(rates) if rates else 0,
                    'funding_rate_trend': 'positive' if rates[-1] > sum(rates[:-1])/len(rates[:-1]) else 'negative' if rates else 'neutral'
                }
        except Exception as e:
            print(f"❌ Funding History error: {e}")
            return {}
    
    def fetch_oi_history(self, symbol: str) -> Dict[str, Any]:
        """Fetch open interest history"""
        try:
            to_ts = int(time.time())
            from_ts = to_ts - (7 * 24 * 3600)  # Last 7 days
            
            oi_history = self._coinalyze_get("/open-interest-history", {
                "symbols": symbol,
                "interval": "4hour",
                "from": from_ts,
                "to": to_ts,
                "convert_to_usd": "true"
            })
            
            if oi_history and oi_history[0]['history']:
                history = oi_history[0]['history']
                oi_values = [h.get('c', h.get('value', 0)) for h in history]
                
                return {
                    'oi_history_7d': oi_values,
                    'oi_trend': 'increasing' if oi_values[-1] > oi_values[0] else 'decreasing',
                    'oi_volatility': max(oi_values) - min(oi_values) if oi_values else 0
                }
        except Exception as e:
            print(f"❌ OI History error: {e}")
            return {}
    
    def _build_pattern_context(self, data):
        """Build pattern analysis context from available data"""
        context_parts = []
        
        # L/S Ratio Pattern Analysis
        positioning_data = data.get('positioning', {})
        if positioning_data.get('ls_ratio_history'):
            ls_history = positioning_data['ls_ratio_history']
            current_ls = positioning_data.get('current_ls_ratio', 0)
            avg_ls = positioning_data.get('avg_ls_ratio_24h', 0)
            
            if len(ls_history) >= 5:
                # Compare current vs recent values
                recent_avg = sum(ls_history[-5:]) / 5
                change_pct = ((current_ls - recent_avg) / recent_avg * 100) if recent_avg > 0 else 0
                
                direction = "📈" if change_pct > 5 else "📉" if change_pct < -5 else "➡️"
                context_parts.append(
                    f"📊 L/S RATIO TREND: {current_ls:.2f} vs {recent_avg:.2f} recent avg ({change_pct:+.1f}%) {direction}"
                )
        
        # OI Pattern Analysis
        oi_data = data.get('open_interest', {})
        if oi_data.get('oi_history'):
            oi_history = oi_data['oi_history']
            if len(oi_history) >= 12:  # 12 hours of data
                # Compare recent vs earlier values
                recent_oi = sum(oi_history[-6:]) / 6  # Last 6 hours
                earlier_oi = sum(oi_history[-12:-6]) / 6  # 6-12 hours ago
                oi_change = ((recent_oi - earlier_oi) / earlier_oi * 100) if earlier_oi > 0 else 0
                
                direction = "📈" if oi_change > 3 else "📉" if oi_change < -3 else "➡️"
                context_parts.append(
                    f"🏦 OI MOMENTUM: Recent 6h avg vs prior 6h ({oi_change:+.1f}%) {direction}"
                )
        
        # Funding Rate Pattern
        funding_history = data.get('funding_history', {})
        if funding_history.get('funding_rate_history'):
            fr_history = funding_history['funding_rate_history']
            if len(fr_history) >= 3:
                current_fr = fr_history[-1]
                avg_fr = sum(fr_history[-3:]) / 3
                trend = funding_history.get('funding_rate_trend', 'neutral')
                
                context_parts.append(
                    f"💸 FUNDING TREND: {trend.upper()} pattern, current {current_fr*100:.4f}% vs {avg_fr*100:.4f}% avg"
                )
        
        # Return formatted context or default message
        if context_parts:
            return "\n".join(context_parts)
        else:
            return "Limited historical data available for pattern analysis"
    
    def intelligent_analysis(self, symbol, data):
        """Let AI analyze Coinalyze data with pattern-aware insights"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Extract key metrics for cleaner prompt
        price_data = data.get('prices', {})
        oi_data = data.get('open_interest', {})
        funding_data = data.get('funding', {})
        liq_data = data.get('liquidations', {})
        positioning_data = data.get('positioning', {})
        
        # Enhanced pattern analysis context
        pattern_context = self._build_pattern_context(data)
        
        prompt = f"""
        🎯 {symbol.upper()} DERIVATIVES • {datetime.now(timezone.utc).strftime('%H:%M UTC')}
        
        📊 CURRENT SNAPSHOT:
        💰 ${price_data.get('current_price', 0):.2f} | OI: ${oi_data.get('current_oi_usd', 0)/1e6:.1f}M ({oi_data.get('oi_change_24h_pct', 0):+.1f}% 24h)
        💸 Funding: {funding_data.get('current_funding_rate_pct', 0):.4f}% | L/S: {positioning_data.get('current_ls_ratio', 0):.2f}
        
        🔍 PATTERN ANALYSIS:
        {pattern_context}
        
        DETAILED METRICS:
        
        PRICE & VOLUME:
        - Current: ${price_data.get('current_price', 0):.2f} ({price_data.get('price_change_24h', 0):+.2f}% 24h)
        - Range: ${price_data.get('low_24h', 0):.2f} - ${price_data.get('high_24h', 0):.2f}
        - Volume: {price_data.get('volume_24h', 0):,.0f}
        
        OPEN INTEREST:
        - Current OI: ${oi_data.get('current_oi_usd', 0):,.0f}
        - OI Change 24h: {oi_data.get('oi_change_24h_pct', 0):+.2f}%
        
        FUNDING:
        - Current Rate: {funding_data.get('current_funding_rate_pct', 0):.4f}%
        - Predicted Rate: {funding_data.get('predicted_funding_rate_pct', 0):.4f}%
        
        LIQUIDATIONS (24h):
        - Long: ${liq_data.get('liquidations_long_24h_usd', 0):,.0f} | Short: ${liq_data.get('liquidations_short_24h_usd', 0):,.0f}
        - Ratio: {liq_data.get('liquidation_ratio', 0):.2f}
        
        POSITIONING:
        - Current L/S: {positioning_data.get('current_ls_ratio', 0):.2f}
        - Average L/S 24h: {positioning_data.get('avg_ls_ratio_24h', 0):.2f}
        - L/S History: {positioning_data.get('ls_ratio_history', [])[-5:] if positioning_data.get('ls_ratio_history') else 'No data'}
        
        ═══════════════════════════════════════════════════════════════════════════════
        📋 ANALYSIS REQUIREMENTS:
        
        Focus on PATTERNS and TRENDS, not just current values. Provide:
        
        🎯 BIAS: BULLISH / BEARISH / NEUTRAL / UNCLEAR
        
        📊 KEY INSIGHT: The most significant pattern change that reveals market sentiment and positioning shifts. What does the data tell us about trader behavior?
        
        ⚠️ TOP RISK: Highest probability risk based on current patterns (liquidation cascade, funding squeeze, positioning reversal)
        
        💡 ACTION: Specific recommendation with entry levels, targets, and risk management
        
        CRITICAL:
        - Emphasize what has CHANGED in the patterns
        - Explain what these changes indicate about market dynamics
        - Provide specific price levels and risk management
        - Consider derivatives-specific risks and opportunities
        
        Current price reference: ${price_data.get('current_price', 0):.2f}
        """
        
        try:
            # Use full o3 model for superior pattern analysis and market insights
            print("🧠 Engaging o3 model for comprehensive pattern-aware analysis...")
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an elite cryptocurrency derivatives trader and quantitative analyst with 25+ years of experience across traditional finance and digital assets. You have advanced expertise in market microstructure, derivatives pricing, systematic trading, and behavioral finance. You excel at identifying subtle patterns, trend reversals, and market regime changes that others miss. Your analysis combines technical precision with deep understanding of trader psychology and market dynamics. Use your superior reasoning capabilities to provide institutional-grade insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=2000  # More tokens for comprehensive o3 analysis
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"⚠️ o3 model error: {e}")
            # Fallback hierarchy: o3-mini -> GPT-4
            try:
                print("🔄 Falling back to o3-mini...")
                response = client.chat.completions.create(
                    model="o3-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert cryptocurrency derivatives trader specializing in futures and perpetual swaps. Focus on derivatives-specific analysis using open interest, funding rates, liquidations, and positioning data."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=1000
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
                                "content": "You are an expert cryptocurrency derivatives trader. Provide specific trading recommendations based on derivatives data."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=800,
                        temperature=0.2
                    )
                    return response.choices[0].message.content
                except Exception as final_e:
                    return f"AI analysis unavailable. o3 error: {e}, o3-mini error: {fallback_e}, GPT-4 error: {final_e}"

def analyze_crypto_intelligently(symbol="SOL"):
    """Main function for intelligent Coinalyze-only crypto analysis"""
    print(f"🤖 Starting Coinalyze-Only Analysis for {symbol.upper()}...")
    
    try:
        agent = AdvancedCryptoAgent()
        
        # Let AI decide what Coinalyze metrics to fetch
        data = agent.fetch_intelligent_data(symbol)
        
        print(f"\n📊 Coinalyze data collection complete for {symbol.upper()}!")
        
        # Display key metrics
        if data.get('prices'):
            price_data = data['prices']
            print(f"💰 Current Price: ${price_data.get('current_price', 0):.2f}")
            print(f"📈 24h Change: {price_data.get('price_change_24h', 0):+.2f}%")
        
        if data.get('open_interest'):
            oi_data = data['open_interest']
            print(f"🏦 Open Interest: ${oi_data.get('current_oi_usd', 0):,.0f}")
        
        if data.get('funding'):
            funding_data = data['funding']
            print(f"💸 Funding Rate: {funding_data.get('current_funding_rate_pct', 0):.4f}%")
        
        # Let AI analyze everything
        analysis = agent.intelligent_analysis(symbol, data)
        
        print("\n" + "="*80)
        print(f"🧠 COINALYZE DERIVATIVES ANALYSIS - {symbol.upper()}")
        print("="*80)
        print(analysis)
        print("\n" + "="*80)
        print("🤖 Analysis powered by Coinalyze API + AI")
        print("📊 Data source: https://api.coinalyze.net/v1/doc/")
        print("⚠️  For educational purposes only - not financial advice")
        
        return {
            'symbol': symbol,
            'data': data,
            'analysis': analysis,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_source': 'Coinalyze API'
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Coinalyze-only crypto analysis")
    parser.add_argument("--symbol", "-s", default="SOL", help="Crypto symbol to analyze")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    args = parser.parse_args()
    
    # Analyze crypto intelligently
    result = analyze_crypto_intelligently(args.symbol)
    
    if result and args.json:
        print("\n" + "="*50)
        print("RAW JSON OUTPUT:")
        print("="*50)
        print(json.dumps(result, indent=2))
    
    if result and args.save:
        filename = f"analysis_{args.symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"📁 Results saved to {filename}")
    
    print("\n✅ Intelligent analysis complete!")
    print("💾 Full results saved to intelligent_analysis.json")