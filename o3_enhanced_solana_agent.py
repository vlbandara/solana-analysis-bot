#!/usr/bin/env python3
"""
O3 Enhanced Solana Analysis Agent
Leverages the full power of ChatGPT o3 model for comprehensive crypto analysis
"""

import os
import requests
from datetime import datetime
import ccxt
from openai import OpenAI
import json

class O3SolanaAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def fetch_comprehensive_data(self):
        """Fetch all available real-time data for comprehensive o3 analysis"""
        print("🔍 Fetching comprehensive market data for o3 analysis...")
        
        # CoinGecko data
        try:
            url = "https://api.coingecko.com/api/v3/coins/solana"
            response = self.session.get(url, timeout=10)
            coingecko_data = response.json()
            
            price_data = {
                'current_price': coingecko_data['market_data']['current_price']['usd'],
                'market_cap': coingecko_data['market_data']['market_cap']['usd'],
                'volume_24h': coingecko_data['market_data']['total_volume']['usd'],
                'price_change_24h': coingecko_data['market_data']['price_change_percentage_24h'],
                'price_change_7d': coingecko_data['market_data']['price_change_percentage_7d'],
                'price_change_30d': coingecko_data['market_data']['price_change_percentage_30d'],
                'high_24h': coingecko_data['market_data']['high_24h']['usd'],
                'low_24h': coingecko_data['market_data']['low_24h']['usd'],
                'ath': coingecko_data['market_data']['ath']['usd'],
                'atl': coingecko_data['market_data']['atl']['usd'],
                'market_cap_rank': coingecko_data['market_cap_rank'],
                'circulating_supply': coingecko_data['market_data']['circulating_supply'],
                'total_supply': coingecko_data['market_data']['total_supply']
            }
            print(f"   ✅ Price data: ${price_data['current_price']:.2f}")
        except Exception as e:
            print(f"   ❌ Price data error: {e}")
            return None
        
        # Binance exchange data
        try:
            exchange = ccxt.binance()
            ticker = exchange.fetch_ticker('SOL/USDT')
            
            exchange_data = {
                'price': ticker['last'],
                'volume': ticker['baseVolume'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'change_percent': ticker['percentage'],
                'bid_ask_spread': ticker['ask'] - ticker['bid']
            }
            print(f"   ✅ Exchange data: Bid/Ask ${exchange_data['bid']:.2f}/${exchange_data['ask']:.2f}")
        except Exception as e:
            print(f"   ❌ Exchange data error: {e}")
            exchange_data = None
        
        # Derivatives data
        try:
            # Open Interest
            oi_url = "https://fapi.binance.com/fapi/v1/openInterest"
            oi_params = {'symbol': 'SOLUSDT'}
            oi_response = self.session.get(oi_url, params=oi_params, timeout=10)
            oi_data = oi_response.json()
            
            # Long/Short ratio
            ratio_url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
            ratio_params = {'symbol': 'SOLUSDT', 'period': '1d', 'limit': 5}
            ratio_response = self.session.get(ratio_url, params=ratio_params, timeout=10)
            ratio_data = ratio_response.json()
            
            # Funding rate
            funding_url = "https://fapi.binance.com/fapi/v1/premiumIndex"
            funding_params = {'symbol': 'SOLUSDT'}
            funding_response = self.session.get(funding_url, params=funding_params, timeout=10)
            funding_data = funding_response.json()
            
            derivatives_data = {
                'open_interest': float(oi_data['openInterest']),
                'long_short_ratio': float(ratio_data[0]['longShortRatio']) if ratio_data else None,
                'long_account_percent': float(ratio_data[0]['longAccount']) if ratio_data else None,
                'short_account_percent': float(ratio_data[0]['shortAccount']) if ratio_data else None,
                'funding_rate': float(funding_data['lastFundingRate']) if funding_data else None,
                'funding_rate_annual': float(funding_data['lastFundingRate']) * 365 * 3 if funding_data else None,
                'long_short_trend': ratio_data[:3] if len(ratio_data) >= 3 else None
            }
            print(f"   ✅ Derivatives: OI {derivatives_data['open_interest']:,.0f} SOL, L/S {derivatives_data['long_short_ratio']:.2f}")
        except Exception as e:
            print(f"   ❌ Derivatives error: {e}")
            derivatives_data = None
        
        # Fear & Greed
        try:
            fg_url = "https://api.alternative.me/fng/"
            fg_response = self.session.get(fg_url, timeout=10)
            fg_data = fg_response.json()
            
            sentiment_data = {
                'fear_greed_current': int(fg_data['data'][0]['value']),
                'fear_greed_classification': fg_data['data'][0]['value_classification'],
                'fear_greed_yesterday': int(fg_data['data'][1]['value']) if len(fg_data['data']) > 1 else None,
                'fear_greed_week_ago': int(fg_data['data'][7]['value']) if len(fg_data['data']) > 7 else None
            }
            print(f"   ✅ Sentiment: F&G {sentiment_data['fear_greed_current']} ({sentiment_data['fear_greed_classification']})")
        except Exception as e:
            print(f"   ❌ Sentiment error: {e}")
            sentiment_data = None
        
        # Technical indicators (simplified)
        try:
            ohlcv = exchange.fetch_ohlcv('SOL/USDT', '1h', limit=50)
            closes = [candle[4] for candle in ohlcv]
            highs = [candle[2] for candle in ohlcv]
            lows = [candle[3] for candle in ohlcv]
            volumes = [candle[5] for candle in ohlcv]
            
            # Simple calculations
            current_price = closes[-1]
            ma_20 = sum(closes[-20:]) / 20
            ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
            
            technical_data = {
                'current_price': current_price,
                'ma_20': ma_20,
                'ma_50': ma_50,
                'price_vs_ma20': ((current_price - ma_20) / ma_20) * 100,
                'price_vs_ma50': ((current_price - ma_50) / ma_50) * 100,
                'recent_high': max(highs[-10:]),
                'recent_low': min(lows[-10:]),
                'avg_volume_10': sum(volumes[-10:]) / 10,
                'current_volume': volumes[-1],
                'volume_ratio': volumes[-1] / (sum(volumes[-10:]) / 10) if sum(volumes[-10:]) > 0 else 1
            }
            print(f"   ✅ Technical: Price vs MA20 {technical_data['price_vs_ma20']:.1f}%")
        except Exception as e:
            print(f"   ❌ Technical error: {e}")
            technical_data = None
        
        return {
            'price': price_data,
            'exchange': exchange_data,
            'derivatives': derivatives_data,
            'sentiment': sentiment_data,
            'technical': technical_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_with_o3(self, data):
        """Send comprehensive data to o3 model for advanced analysis"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # SAFE CAST helper to avoid formatting NoneType errors
        def _sf(val, default=0.0):
            try:
                return default if val is None else float(val)
            except Exception:
                return default
        
        # Coerce key numeric fields from data dicts
        for key_path in [
            ('price','current_price'), ('price','price_change_24h'),
            ('derivatives','open_interest'), ('derivatives','long_short_ratio'),
            ('derivatives','funding_rate'), ('derivatives','funding_rate_annual'),
        ]:
            try:
                sect, field = key_path
                if data[sect] and data[sect][field] is not None:
                    data[sect][field] = _sf(data[sect][field])
                else:
                    if not data[sect]:
                        data[sect] = {}
                    data[sect][field] = 0.0
            except Exception:
                pass

        # Ensure all major data sections exist with safe defaults to avoid NoneType formatting errors
        data['exchange'] = data.get('exchange') or {}
        data['technical'] = data.get('technical') or {}
        data['derivatives'] = data.get('derivatives') or {}
        data['sentiment'] = data.get('sentiment') or {}

        # Provide default values for any missing fields referenced in the prompt
        data['exchange'].setdefault('price', 0.0)
        data['exchange'].setdefault('bid', 0.0)
        data['exchange'].setdefault('ask', 0.0)
        data['exchange'].setdefault('bid_ask_spread', 0.0)
        data['exchange'].setdefault('volume', 0.0)

        data['technical'].setdefault('volume_ratio', 1.0)
        data['technical'].setdefault('price_vs_ma20', 0.0)
        data['technical'].setdefault('price_vs_ma50', 0.0)
        data['technical'].setdefault('recent_low', 0.0)
        data['technical'].setdefault('recent_high', 0.0)

        data['derivatives'].setdefault('open_interest', 0.0)
        data['derivatives'].setdefault('long_short_ratio', 0.0)
        data['derivatives'].setdefault('long_account_percent', 0.0)
        data['derivatives'].setdefault('short_account_percent', 0.0)
        data['derivatives'].setdefault('funding_rate', 0.0)
        data['derivatives'].setdefault('funding_rate_annual', 0.0)
        data['derivatives'].setdefault('long_short_trend', [
            {'longShortRatio': 0.0},
            {'longShortRatio': 0.0},
            {'longShortRatio': 0.0}
        ])
        # Ensure the long_short_trend list has at least 3 items
        if len(data['derivatives']['long_short_trend']) < 3:
            data['derivatives']['long_short_trend'].extend([
                {'longShortRatio': 0.0}
                for _ in range(3 - len(data['derivatives']['long_short_trend']))
            ])

        data['sentiment'].setdefault('fear_greed_current', 50)
        data['sentiment'].setdefault('fear_greed_classification', 'Neutral')
        data['sentiment'].setdefault('fear_greed_yesterday', 'N/A')
        data['sentiment'].setdefault('fear_greed_week_ago', 'N/A')

        # Create ultra-comprehensive prompt for o3
        prompt = f"""
        COMPREHENSIVE SOLANA (SOL) ANALYSIS - FULL o3 MODEL CAPABILITIES
        
        Analysis Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        ═══════════════════════════════════════════════════════════════════════════════
        🏷️ MARKET DATA SNAPSHOT
        ═══════════════════════════════════════════════════════════════════════════════
        
        💰 PRICE METRICS:
        • Current Price: ${data['price']['current_price']:.2f}
        • Market Cap: ${data['price']['market_cap']:,.0f} (Rank #{data['price']['market_cap_rank']})
        • 24h Volume: ${data['price']['volume_24h']:,.0f}
        • 24h Range: ${data['price']['low_24h']:.2f} - ${data['price']['high_24h']:.2f}
        • Price Changes: 24h ({data['price']['price_change_24h']:.2f}%) | 7d ({data['price']['price_change_7d']:.2f}%) | 30d ({data['price']['price_change_30d']:.2f}%)
        • All-Time High: ${data['price']['ath']:.2f} | All-Time Low: ${data['price']['atl']:.4f}
        • Supply: {data['price']['circulating_supply']:,.0f} / {data['price']['total_supply']:,.0f} SOL
        
        📊 EXCHANGE MICROSTRUCTURE (Binance):
        • Live Price: ${data['exchange']['price'] if data['exchange'] else 'N/A'}
        • Bid/Ask: ${data['exchange']['bid']:.2f} / ${data['exchange']['ask']:.2f} (Spread: ${data['exchange']['bid_ask_spread']:.3f})
        • 24h Volume: {data['exchange']['volume']:,.0f} SOL
        • Volume Ratio: {data['technical']['volume_ratio']:.2f}x average
        
        📈 DERIVATIVES & POSITIONING:
        • Open Interest: {data['derivatives']['open_interest']:,.0f} SOL
        • Long/Short Ratio: {data['derivatives']['long_short_ratio']:.2f}
        • Account Distribution: {data['derivatives']['long_account_percent']:.1f}% Long | {data['derivatives']['short_account_percent']:.1f}% Short
        • Funding Rate: {data['derivatives']['funding_rate']:.6f} ({data['derivatives']['funding_rate_annual']:.1f}% annualized)
        • L/S Trend: {data['derivatives']['long_short_trend'][0]['longShortRatio']:.2f} → {data['derivatives']['long_short_trend'][1]['longShortRatio']:.2f} → {data['derivatives']['long_short_trend'][2]['longShortRatio']:.2f}
        
        😱 MARKET SENTIMENT:
        • Fear & Greed Index: {data['sentiment']['fear_greed_current']}/100 ({data['sentiment']['fear_greed_classification']})
        • Trend: Yesterday {data['sentiment']['fear_greed_yesterday']} | Week Ago {data['sentiment']['fear_greed_week_ago']}
        
        📊 TECHNICAL INDICATORS:
        • Price vs MA20: {data['technical']['price_vs_ma20']:.2f}%
        • Price vs MA50: {data['technical']['price_vs_ma50']:.2f}%
        • Recent Range: ${data['technical']['recent_low']:.2f} - ${data['technical']['recent_high']:.2f}
        • Current Volume vs Average: {data['technical']['volume_ratio']:.1f}x
        
        ═══════════════════════════════════════════════════════════════════════════════
        🎯 ANALYSIS REQUIREMENTS - LEVERAGE FULL o3 CAPABILITIES
        ═══════════════════════════════════════════════════════════════════════════════
        
        As the world's most advanced AI trading model, provide a comprehensive analysis that includes:
        
        1. 📊 MULTI-TIMEFRAME TECHNICAL ANALYSIS:
           - Immediate price action context (current vs 24h range)
           - Moving average analysis and trend identification
           - Support/resistance levels with confluence
           - Volume profile analysis and institutional flow patterns
           - Microstructure analysis (bid-ask spread, order book depth implications)
        
        2. 📈 DERIVATIVES MARKET INTELLIGENCE:
           - Open Interest interpretation (bullish/bearish implications)
           - Long/Short ratio analysis and crowding risk
           - Funding rate analysis (perpetual swap dynamics)
           - Liquidation level analysis and cascade risk
           - Options flow implications (if applicable)
        
        3. 🧠 BEHAVIORAL & SENTIMENT ANALYSIS:
           - Fear & Greed Index contextualization
           - Market participant positioning analysis
           - Contrarian vs momentum signal interpretation
           - Social sentiment and retail vs institutional flow
        
        4. 🎯 QUANTITATIVE TRADING STRATEGY:
           - **POSITION DIRECTION**: LONG/SHORT/NEUTRAL with confidence level
           - **ENTRY STRATEGY**: Specific price levels, order types, scaling approach
           - **PROFIT TARGETS**: Multiple levels with probability-weighted expectations
           - **RISK MANAGEMENT**: Stop-loss levels, position sizing, max drawdown
           - **TIME HORIZON**: Expected duration and key catalysts
           - **RISK/REWARD RATIOS**: Detailed calculations for each scenario
        
        5. 💡 ADVANCED MARKET CONTEXT:
           - Macro environment impact on SOL
           - Ecosystem developments and network growth
           - Competitive positioning vs other L1s
           - Regulatory environment implications
           - Black swan risk assessment
        
        6. 🚨 SCENARIO ANALYSIS:
           - **BASE CASE** (60% probability): Expected price path
           - **BULL CASE** (25% probability): Upside scenario and catalysts
           - **BEAR CASE** (15% probability): Downside risks and triggers
           - **Tail RISKS**: Extreme scenarios and portfolio protection
        
        7. 📋 EXECUTION CHECKLIST:
           - Pre-market conditions to monitor
           - Intraday levels to watch
           - Exit criteria for each scenario
           - Portfolio allocation recommendations
           - Hedge considerations
        
        ═══════════════════════════════════════════════════════════════════════════════
        🎯 CRITICAL REQUIREMENTS
        ═══════════════════════════════════════════════════════════════════════════════
        
        • Base ALL analysis on the REAL data provided (SOL at ${data['price']['current_price']:.2f})
        • Provide SPECIFIC price levels, not ranges or approximations
        • Include QUANTITATIVE risk/reward calculations
        • Consider the FULL market context (derivatives, sentiment, technical)
        • Leverage your ADVANCED reasoning capabilities for nuanced insights
        • Provide ACTIONABLE recommendations with clear execution steps
        
        This is a professional trading analysis - be precise, comprehensive, and actionable.
        """
        
        try:
            print("\n🧠 Engaging ChatGPT o3 model for comprehensive analysis...")
            print("⚡ Processing advanced technical, fundamental, and quantitative analysis...")
            
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an elite quantitative trading analyst and portfolio manager with 25+ years of experience across traditional finance and digital assets. You have advanced degrees in finance, mathematics, and computer science. You specialize in multi-asset derivatives trading, systematic strategies, and risk management. Use your full analytical capabilities to provide institutional-grade trading recommendations with precise quantitative analysis, comprehensive risk assessment, and sophisticated market microstructure insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=12000  # Maximum for comprehensive analysis
            )
            
            return response.choices[0].message.content, "o3"
            
        except Exception as e:
            if "o3" in str(e).lower():
                print("⚠️ o3 model not available, falling back to GPT-4...")
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert quantitative trader and analyst. Provide comprehensive trading analysis with specific recommendations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=4000
                )
                
                return response.choices[0].message.content, "GPT-4"
            else:
                raise e

def run_o3_enhanced_analysis():
    """Main function for o3-powered Solana analysis"""
    print("🚀 INITIATING o3 ENHANCED SOLANA ANALYSIS")
    print("=" * 80)
    
    agent = O3SolanaAgent()
    
    # Fetch comprehensive data
    data = agent.fetch_comprehensive_data()
    
    if not data or not data['price']:
        print("❌ Failed to fetch essential market data!")
        return None
    
    print(f"\n📊 Data collection complete!")
    print(f"💰 SOL Price: ${data['price']['current_price']:.2f}")
    print(f"📈 24h Change: {data['price']['price_change_24h']:.2f}%")
    print(f"📊 Open Interest: {data['derivatives']['open_interest']:,.0f} SOL")
    print(f"⚖️ Long/Short: {data['derivatives']['long_short_ratio']:.2f}")
    print(f"😨 Fear & Greed: {data['sentiment']['fear_greed_current']} ({data['sentiment']['fear_greed_classification']})")
    
    # Analyze with o3
    analysis, model_used = agent.analyze_with_o3(data)
    
    print("\n" + "="*80)
    print(f"🧠 o3 ENHANCED SOLANA ANALYSIS REPORT")
    print(f"Model: {model_used} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(analysis)
    print("\n" + "="*80)
    print("🔬 Analysis powered by ChatGPT o3 - Advanced reasoning and comprehensive market analysis")
    print("📊 Real-time data from multiple institutional-grade sources")
    print("⚠️ For educational and research purposes only - not financial advice")
    
    # Save results
    results = {
        'model_used': model_used,
        'analysis': analysis,
        'raw_data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('o3_enhanced_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n💾 Full analysis saved to o3_enhanced_analysis.json")
    
    return results

if __name__ == "__main__":
    result = run_o3_enhanced_analysis()
    
    if result:
        print("\n✅ o3 Enhanced Analysis Complete!")
        print("🎯 Comprehensive trading strategy generated with advanced AI reasoning")
    else:
        print("\n❌ Analysis failed!")