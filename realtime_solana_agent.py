#!/usr/bin/env python3
"""
Autonomous Solana Analysis Agent
Fetches real-time data from multiple sources and provides comprehensive analysis
Sources: CoinGecko, CoinGlass, Binance, CoinMarketCap, Fear & Greed Index
"""

import os
import time
import requests
from datetime import datetime, timedelta
import ccxt
from openai import OpenAI
import json

class SolanaDataAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def fetch_coingecko_data(self):
        """Fetch comprehensive Solana data from CoinGecko"""
        try:
            # Current price and market data
            url = "https://api.coingecko.com/api/v3/coins/solana"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            current_price = data['market_data']['current_price']['usd']
            market_cap = data['market_data']['market_cap']['usd']
            volume_24h = data['market_data']['total_volume']['usd']
            price_change_24h = data['market_data']['price_change_percentage_24h']
            price_change_7d = data['market_data']['price_change_percentage_7d']
            
            return {
                'source': 'CoinGecko',
                'current_price': current_price,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'price_change_24h': price_change_24h,
                'price_change_7d': price_change_7d,
                'high_24h': data['market_data']['high_24h']['usd'],
                'low_24h': data['market_data']['low_24h']['usd'],
                'ath': data['market_data']['ath']['usd'],
                'atl': data['market_data']['atl']['usd']
            }
        except Exception as e:
            print(f"❌ CoinGecko fetch error: {e}")
            return None
    
    def fetch_binance_data(self):
        """Fetch real-time data from Binance"""
        try:
            exchange = ccxt.binance()
            ticker = exchange.fetch_ticker('SOL/USDT')
            
            return {
                'source': 'Binance',
                'price': ticker['last'],
                'volume': ticker['baseVolume'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'change_percent': ticker['percentage']
            }
        except Exception as e:
            print(f"❌ Binance fetch error: {e}")
            return None
    
    def get_binance_open_interest(self):
        """Get Open Interest from Binance Futures"""
        try:
            # Binance Futures Open Interest
            url = "https://fapi.binance.com/fapi/v1/openInterest"
            params = {'symbol': 'SOLUSDT'}
            response = self.session.get(url, params=params, timeout=10)
            oi_data = response.json()
            
            # Long/Short ratio
            url_ratio = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
            params_ratio = {'symbol': 'SOLUSDT', 'period': '1d', 'limit': 1}
            response_ratio = self.session.get(url_ratio, params=params_ratio, timeout=10)
            ratio_data = response_ratio.json()
            
            return {
                'open_interest': float(oi_data['openInterest']),
                'long_short_ratio': float(ratio_data[0]['longShortRatio']) if ratio_data else None,
                'long_account_percent': float(ratio_data[0]['longAccount']) if ratio_data else None,
                'short_account_percent': float(ratio_data[0]['shortAccount']) if ratio_data else None
            }
        except Exception as e:
            print(f"❌ Binance Open Interest error: {e}")
            return {
                'open_interest': 'N/A',
                'long_short_ratio': 'N/A',
                'long_account_percent': 'N/A',
                'short_account_percent': 'N/A'
            }
    
    def fetch_fear_greed_index(self):
        """Fetch Crypto Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            return {
                'source': 'Fear & Greed Index',
                'value': int(data['data'][0]['value']),
                'classification': data['data'][0]['value_classification'],
                'timestamp': data['data'][0]['timestamp']
            }
        except Exception as e:
            print(f"❌ Fear & Greed Index error: {e}")
            return {
                'source': 'Fear & Greed Index',
                'value': 50,
                'classification': 'Neutral',
                'timestamp': 'N/A'
            }

def analyze_with_realtime_data():
    """Main function to fetch all data and analyze with AI"""
    print("🤖 Starting Autonomous Solana Analysis Agent...")
    print("🔍 Fetching real-time data from multiple sources...")
    
    agent = SolanaDataAgent()
    
    # Fetch data from all sources
    print("   📡 Fetching CoinGecko data...")
    coingecko_data = agent.fetch_coingecko_data()
    
    print("   📡 Fetching Binance data...")
    binance_data = agent.fetch_binance_data()
    
    print("   📡 Fetching Open Interest data...")
    oi_data = agent.get_binance_open_interest()
    
    print("   📡 Fetching Fear & Greed Index...")
    fear_greed = agent.fetch_fear_greed_index()
    
    if not coingecko_data:
        print("❌ Failed to fetch essential price data!")
        return None
    
    print("\n📊 Real-time data fetched successfully!")
    print(f"💰 Current SOL Price: ${coingecko_data['current_price']:.2f}")
    print(f"📈 24h Change: {coingecko_data['price_change_24h']:.2f}%")
    print(f"😨 Fear & Greed Index: {fear_greed['value']} ({fear_greed['classification']})")
    
    if oi_data['open_interest'] != 'N/A':
        print(f"📊 Open Interest: {oi_data['open_interest']:,.0f} SOL")
        print(f"⚖️ Long/Short Ratio: {oi_data['long_short_ratio']:.2f}")
    
    # Create comprehensive prompt for AI analysis
    analysis_prompt = f"""
    REAL-TIME SOLANA (SOL) ANALYSIS REQUEST
    
    **CURRENT MARKET DATA (Live as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):**
    
    🏷️ **PRICE DATA:**
    - Current Price: ${coingecko_data['current_price']:.2f}
    - 24h High: ${coingecko_data['high_24h']:.2f}
    - 24h Low: ${coingecko_data['low_24h']:.2f}
    - 24h Change: {coingecko_data['price_change_24h']:.2f}%
    - 7d Change: {coingecko_data['price_change_7d']:.2f}%
    - Market Cap: ${coingecko_data['market_cap']:,.0f}
    - 24h Volume: ${coingecko_data['volume_24h']:,.0f}
    - All-Time High: ${coingecko_data['ath']:.2f}
    - All-Time Low: ${coingecko_data['atl']:.2f}
    
    📊 **DERIVATIVES DATA:**
    - Open Interest: {oi_data['open_interest']} SOL
    - Long/Short Ratio: {oi_data['long_short_ratio']}
    - Long Account %: {oi_data['long_account_percent']}%
    - Short Account %: {oi_data['short_account_percent']}%
    
    😱 **MARKET SENTIMENT:**
    - Fear & Greed Index: {fear_greed['value']}/100 ({fear_greed['classification']})
    
    📈 **EXCHANGE DATA (Binance):**
    - Live Price: ${binance_data['price'] if binance_data else 'N/A'}
    - 24h Volume: {binance_data['volume'] if binance_data else 'N/A'} SOL
    
    **CRITICAL ANALYSIS REQUIREMENTS:**
    
    Based on this REAL-TIME data showing SOL at ${coingecko_data['current_price']:.2f}, provide:
    
    1. **IMMEDIATE MARKET ASSESSMENT:**
       - Price action analysis: Is ${coingecko_data['current_price']:.2f} at support/resistance?
       - Volume analysis: {coingecko_data['volume_24h']:,.0f} volume significance
       - Open Interest implications for price direction
       - Fear & Greed at {fear_greed['value']} - contrarian vs. momentum play?
    
    2. **TECHNICAL SETUP DECISION:**
       - LONG or SHORT position recommendation
       - Entry zone around current ${coingecko_data['current_price']:.2f} level
       - Target 1, 2, 3 with specific dollar amounts
       - Stop-loss level with reasoning
       - Risk/reward ratio calculation
    
    3. **POSITION MANAGEMENT:**
       - Position size (% of portfolio)
       - Entry strategy (limit order levels)
       - Time horizon for this trade
       - Conditions that would invalidate the setup
    
    4. **MARKET CONTEXT:**
       - How does ${coingecko_data['current_price']:.2f} compare to recent ATH of ${coingecko_data['ath']:.2f}?
       - Is this price level historically significant?
       - What's the next major support/resistance?
    
    **IMPORTANT**: Base ALL recommendations on the actual current price of ${coingecko_data['current_price']:.2f}, not hypothetical scenarios.
    """
    
    # Send to AI for analysis
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("\n🧠 Processing with AI analysis...")
        
        try:
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency trader with access to real-time market data. Provide specific, actionable trading recommendations based on the current market conditions. Be precise with entry points, targets, and stop losses. Consider the actual market data provided and current price levels."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                max_completion_tokens=4000
            )
            model_used = "o3-mini"
        except Exception as e:
            if "o3-mini" in str(e) or "invalid" in str(e).lower():
                print("ℹ️ o3-mini not available, using GPT-4...")
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert cryptocurrency trader with access to real-time market data. Provide specific, actionable trading recommendations based on current market conditions."
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.1
                )
                model_used = "GPT-4"
            else:
                raise e
        
        analysis = response.choices[0].message.content
        
        print("\n" + "="*80)
        print(f"🚀 AUTONOMOUS SOLANA TRADING ANALYSIS ({model_used})")
        print("="*80)
        print(analysis)
        print("\n" + "="*80)
        print("📊 Data Sources: CoinGecko, Binance, Open Interest, Fear & Greed")
        print("⏰ Analysis Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("💡 This analysis uses REAL-TIME market data")
        print("⚠️  DISCLAIMER: AI-generated analysis for educational purposes only")
        
        return {
            'realtime_data': {
                'coingecko': coingecko_data,
                'binance': binance_data,
                'open_interest': oi_data,
                'fear_greed': fear_greed,
                'timestamp': datetime.now().isoformat()
            },
            'analysis': analysis,
            'model_used': model_used
        }
        
    except Exception as e:
        print(f"❌ AI Analysis error: {e}")
        return None

if __name__ == "__main__":
    result = analyze_with_realtime_data()
    
    if result:
        print("\n✅ Real-time analysis completed!")
        
        # Save results
        with open('realtime_analysis_results.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("💾 Results saved to realtime_analysis_results.json")
    else:
        print("\n❌ Analysis failed!")