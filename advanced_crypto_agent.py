#!/usr/bin/env python3
"""
Advanced Autonomous Crypto Analysis Agent
Extends capabilities with more data sources and intelligent decision making
"""

import os
import requests
import ccxt
from datetime import datetime
import json
from openai import OpenAI

class AdvancedCryptoAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.data_sources = []
    
    def decide_data_sources_needed(self, crypto_symbol):
        """AI decides what data sources to fetch based on the analysis request"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        As a crypto trading agent, determine what data sources I should fetch for analyzing {crypto_symbol}.
        
        Available data sources:
        1. price_data - Current price, volume, market cap
        2. derivatives_data - Open interest, long/short ratios
        3. social_sentiment - Fear & Greed, social media sentiment  
        4. onchain_metrics - Network activity, whale movements
        5. macro_data - Bitcoin correlation, overall market sentiment
        6. technical_indicators - RSI, MACD, support/resistance
        7. news_events - Recent news affecting the asset
        
        Return only a JSON list of the most important 4-5 sources for a comprehensive analysis.
        Example: ["price_data", "derivatives_data", "social_sentiment", "technical_indicators"]
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
            # Simple parsing - in production you'd use more robust JSON parsing
            if "[" in sources_text and "]" in sources_text:
                import ast
                return ast.literal_eval(sources_text)
            else:
                # Fallback to essential sources
                return ["price_data", "derivatives_data", "social_sentiment", "technical_indicators"]
                
        except Exception as e:
            print(f"⚠️ AI source selection failed: {e}")
            return ["price_data", "derivatives_data", "social_sentiment"]
    
    def fetch_intelligent_data(self, symbol):
        """Fetch data based on AI's decision of what's needed"""
        needed_sources = self.decide_data_sources_needed(symbol)
        print(f"🤖 AI decided to fetch: {', '.join(needed_sources)}")
        
        data = {}
        
        for source in needed_sources:
            if source == "price_data":
                data['price'] = self.fetch_coingecko_data(symbol.lower())
            elif source == "derivatives_data":
                data['derivatives'] = self.fetch_binance_derivatives(symbol)
            elif source == "social_sentiment":
                data['sentiment'] = self.fetch_sentiment_data()
            elif source == "technical_indicators":
                data['technical'] = self.fetch_technical_data(symbol)
            elif source == "onchain_metrics":
                data['onchain'] = self.fetch_onchain_data(symbol)
            elif source == "macro_data":
                data['macro'] = self.fetch_macro_data()
        
        return data
    
    def fetch_coingecko_data(self, symbol):
        """Enhanced CoinGecko data fetching"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            return {
                'current_price': data['market_data']['current_price']['usd'],
                'market_cap': data['market_data']['market_cap']['usd'],
                'volume_24h': data['market_data']['total_volume']['usd'],
                'price_change_24h': data['market_data']['price_change_percentage_24h'],
                'price_change_7d': data['market_data']['price_change_percentage_7d'],
                'price_change_30d': data['market_data']['price_change_percentage_30d'],
                'high_24h': data['market_data']['high_24h']['usd'],
                'low_24h': data['market_data']['low_24h']['usd'],
                'ath': data['market_data']['ath']['usd'],
                'atl': data['market_data']['atl']['usd'],
                'circulating_supply': data['market_data']['circulating_supply'],
                'total_supply': data['market_data']['total_supply']
            }
        except Exception as e:
            print(f"❌ Price data error: {e}")
            return None
    
    def fetch_binance_derivatives(self, symbol):
        """Enhanced derivatives data"""
        try:
            # Open Interest
            url = f"https://fapi.binance.com/fapi/v1/openInterest"
            params = {'symbol': f'{symbol.upper()}USDT'}
            oi_response = self.session.get(url, params=params, timeout=10)
            oi_data = oi_response.json()
            
            # Long/Short ratio
            url_ratio = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
            params_ratio = {'symbol': f'{symbol.upper()}USDT', 'period': '1d', 'limit': 5}
            ratio_response = self.session.get(url_ratio, params=params_ratio, timeout=10)
            ratio_data = ratio_response.json()
            
            # Funding rate
            url_funding = "https://fapi.binance.com/fapi/v1/premiumIndex"
            params_funding = {'symbol': f'{symbol.upper()}USDT'}
            funding_response = self.session.get(url_funding, params=params_funding, timeout=10)
            funding_data = funding_response.json()
            
            return {
                'open_interest': float(oi_data['openInterest']),
                'current_long_short_ratio': float(ratio_data[0]['longShortRatio']) if ratio_data else None,
                'funding_rate': float(funding_data['lastFundingRate']) if funding_data else None,
                'long_short_trend': ratio_data[:3] if len(ratio_data) >= 3 else None
            }
        except Exception as e:
            print(f"❌ Derivatives data error: {e}")
            return None
    
    def fetch_sentiment_data(self):
        """Enhanced sentiment indicators"""
        try:
            # Fear & Greed Index
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            return {
                'fear_greed_current': int(data['data'][0]['value']),
                'fear_greed_classification': data['data'][0]['value_classification'],
                'fear_greed_week_ago': int(data['data'][7]['value']) if len(data['data']) > 7 else None
            }
        except Exception as e:
            print(f"❌ Sentiment data error: {e}")
            return None
    
    def fetch_technical_data(self, symbol):
        """Fetch technical indicators using exchange data"""
        try:
            exchange = ccxt.binance()
            
            # Get OHLCV data for technical analysis
            ohlcv = exchange.fetch_ohlcv(f'{symbol.upper()}/USDT', '1h', limit=100)
            
            if not ohlcv:
                return None
            
            # Simple technical calculations (in production, use TA-Lib)
            closes = [candle[4] for candle in ohlcv[-20:]]  # Last 20 closes
            current_price = closes[-1]
            
            # Simple RSI approximation (not accurate, use TA-Lib in production)
            rsi_approx = 50  # Placeholder
            
            # Moving averages
            ma_20 = sum(closes) / len(closes)
            ma_10 = sum(closes[-10:]) / 10
            
            return {
                'current_price': current_price,
                'ma_20': ma_20,
                'ma_10': ma_10,
                'price_vs_ma20': ((current_price - ma_20) / ma_20) * 100,
                'short_term_trend': 'bullish' if ma_10 > ma_20 else 'bearish',
                'rsi_estimate': rsi_approx
            }
        except Exception as e:
            print(f"❌ Technical data error: {e}")
            return None
    
    def intelligent_analysis(self, symbol, data):
        """Let AI analyze all the data and provide recommendations"""
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        data_summary = json.dumps(data, indent=2)
        
        prompt = f"""
        AUTONOMOUS CRYPTO TRADING ANALYSIS
        
        Symbol: {symbol.upper()}
        Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        REAL-TIME DATA COLLECTED:
        {data_summary}
        
        As an expert crypto trader, analyze this comprehensive data and provide:
        
        1. MARKET ASSESSMENT (based on actual data above)
        2. POSITION RECOMMENDATION (LONG/SHORT/WAIT)
        3. SPECIFIC ENTRY POINTS 
        4. PROFIT TARGETS (3 levels)
        5. STOP LOSS LEVELS
        6. POSITION SIZE RECOMMENDATION
        7. TIME HORIZON
        8. RISK/REWARD RATIOS
        9. KEY INVALIDATION LEVELS
        
        Base everything on the ACTUAL data provided. Be specific with dollar amounts and percentages.
        """
        
        try:
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency trader with access to comprehensive real-time market data. Provide specific, actionable trading recommendations with exact price levels. Use advanced technical analysis, market microstructure knowledge, and comprehensive risk assessment."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=8000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            if "o3" in str(e):
                # Fallback to GPT-4
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert cryptocurrency trader. Provide specific trading recommendations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=3000
                )
                return response.choices[0].message.content
            else:
                raise e

def analyze_crypto_intelligently(symbol="SOL"):
    """Main function for intelligent crypto analysis"""
    print(f"🤖 Starting Intelligent Analysis for {symbol.upper()}...")
    
    agent = AdvancedCryptoAgent()
    
    # Let AI decide what data to fetch
    data = agent.fetch_intelligent_data(symbol)
    
    print(f"\n📊 Data collection complete for {symbol.upper()}!")
    
    if data.get('price'):
        print(f"💰 Current Price: ${data['price']['current_price']:.2f}")
        print(f"📈 24h Change: {data['price']['price_change_24h']:.2f}%")
    
    # Let AI analyze everything
    analysis = agent.intelligent_analysis(symbol, data)
    
    print("\n" + "="*80)
    print(f"🧠 INTELLIGENT ANALYSIS REPORT - {symbol.upper()}")
    print("="*80)
    print(analysis)
    print("\n" + "="*80)
    print("🤖 This analysis was generated by an autonomous AI agent")
    print("📊 Data sources were intelligently selected based on analysis requirements")
    print("⚠️  For educational purposes only - not financial advice")
    
    return {
        'symbol': symbol,
        'data': data,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Analyze any crypto intelligently
    result = analyze_crypto_intelligently("SOL")
    
    # Save comprehensive results
    with open('intelligent_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n✅ Intelligent analysis complete!")
    print("💾 Full results saved to intelligent_analysis.json")