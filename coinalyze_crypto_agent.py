#!/usr/bin/env python3
"""
Clean Coinalyze-Only Crypto Analysis Agent
=========================================
Streamlined implementation using ONLY Coinalyze API for comprehensive crypto analysis.
Removes all unnecessary data sources and focuses on derivatives data.

Based on Coinalyze API: https://api.coinalyze.net/v1/doc/

Environment Variables:
- COINALYZE_API_KEY: Get free key from https://coinalyze.net
- OPENAI_API_KEY: For AI analysis (o3-mini or GPT-4 fallback)

Usage:
    python coinalyze_crypto_agent.py
    python coinalyze_crypto_agent.py --symbol BTC
    python coinalyze_crypto_agent.py --symbol ETH --whatsapp
"""

import os
import json
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
import requests
from openai import OpenAI


class CoinalyzeCryptoAgent:
    """Clean crypto analysis agent using only Coinalyze API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('COINALYZE_API_KEY')
        if not self.api_key:
            raise ValueError("COINALYZE_API_KEY required. Get free key from https://coinalyze.net")
        
        self.base_url = "https://api.coinalyze.net/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'api_key': self.api_key,
            'User-Agent': 'CoinalyzeCryptoAgent/1.0'
        })
    
    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make API request to Coinalyze"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Invalid COINALYZE_API_KEY. Check your API key.")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded. Wait before making more requests.")
            else:
                raise ValueError(f"API error {response.status_code}: {e}")
        except Exception as e:
            raise ValueError(f"Request failed: {e}")
    
    def get_supported_symbols(self, market_type: str = "future") -> List[Dict[str, Any]]:
        """Get supported symbols from Coinalyze
        
        Args:
            market_type: 'future' or 'spot'
        """
        endpoint = "/future-markets" if market_type == "future" else "/spot-markets"
        return self._get(endpoint)
    
    def find_symbol(self, crypto: str) -> Tuple[str, str]:
        """Find perpetual and spot symbols for a cryptocurrency
        
        Args:
            crypto: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'SOL')
            
        Returns:
            Tuple of (perp_symbol, spot_symbol)
        """
        # Get supported markets
        future_markets = self.get_supported_symbols("future")
        spot_markets = self.get_supported_symbols("spot")
        
        crypto_upper = crypto.upper()
        
        # Find perpetual contract (prefer USDT, then USD)
        perp_symbol = None
        for market in future_markets:
            if (market['base_asset'] == crypto_upper and 
                market['is_perpetual'] and 
                market['quote_asset'] in ['USDT', 'USD']):
                perp_symbol = market['symbol']
                if market['quote_asset'] == 'USDT':
                    break  # Prefer USDT
        
        # Find spot market
        spot_symbol = None
        for market in spot_markets:
            if (market['base_asset'] == crypto_upper and 
                market['quote_asset'] in ['USDT', 'USD']):
                spot_symbol = market['symbol']
                if market['quote_asset'] == 'USDT':
                    break  # Prefer USDT
        
        if not perp_symbol:
            raise ValueError(f"No perpetual contract found for {crypto}")
        if not spot_symbol:
            print(f"⚠️ No spot market found for {crypto}, using perp for price data")
            spot_symbol = perp_symbol
            
        return perp_symbol, spot_symbol
    
    def get_current_data(self, perp_symbol: str, spot_symbol: str) -> Dict[str, Any]:
        """Get current market data"""
        data = {}
        
        # Current Open Interest
        try:
            oi_data = self._get("/open-interest", {
                "symbols": perp_symbol,
                "convert_to_usd": "true"
            })
            data['open_interest_usd'] = float(oi_data[0]['value']) if oi_data else 0
        except Exception as e:
            print(f"⚠️ Open Interest error: {e}")
            data['open_interest_usd'] = 0
        
        # Current Funding Rate
        try:
            fr_data = self._get("/funding-rate", {"symbols": perp_symbol})
            data['funding_rate'] = float(fr_data[0]['value']) if fr_data else 0
        except Exception as e:
            print(f"⚠️ Funding Rate error: {e}")
            data['funding_rate'] = 0
        
        # Predicted Funding Rate
        try:
            pfr_data = self._get("/predicted-funding-rate", {"symbols": perp_symbol})
            data['predicted_funding_rate'] = float(pfr_data[0]['value']) if pfr_data else 0
        except Exception as e:
            print(f"⚠️ Predicted Funding Rate error: {e}")
            data['predicted_funding_rate'] = 0
        
        return data
    
    def get_historical_data(self, perp_symbol: str, spot_symbol: str, hours: int = 24) -> Dict[str, Any]:
        """Get historical data for analysis"""
        to_ts = int(time.time())
        from_ts = to_ts - (hours * 3600)
        
        base_params = {
            "interval": "1hour",
            "from": from_ts,
            "to": to_ts
        }
        
        data = {}
        
        # Open Interest History
        try:
            oi_hist = self._get("/open-interest-history", {
                **base_params,
                "symbols": perp_symbol,
                "convert_to_usd": "true"
            })
            data['oi_history'] = [float(x.get('c', x.get('value', 0))) for x in oi_hist[0]['history']] if oi_hist else []
        except Exception as e:
            print(f"⚠️ OI History error: {e}")
            data['oi_history'] = []
        
        # Funding Rate History
        try:
            fr_hist = self._get("/funding-rate-history", {**base_params, "symbols": perp_symbol})
            data['fr_history'] = [float(x.get('c', x.get('value', 0))) for x in fr_hist[0]['history']] if fr_hist else []
        except Exception as e:
            print(f"⚠️ FR History error: {e}")
            data['fr_history'] = []
        
        # Liquidation History
        try:
            lq_hist = self._get("/liquidation-history", {
                **base_params,
                "symbols": perp_symbol,
                "convert_to_usd": "true"
            })
            if lq_hist:
                data['liquidations_long'] = [float(x.get('l', 0)) for x in lq_hist[0]['history']]
                data['liquidations_short'] = [float(x.get('s', 0)) for x in lq_hist[0]['history']]
            else:
                data['liquidations_long'] = []
                data['liquidations_short'] = []
        except Exception as e:
            print(f"⚠️ Liquidations error: {e}")
            data['liquidations_long'] = []
            data['liquidations_short'] = []
        
        # Long/Short Ratio History
        try:
            ls_hist = self._get("/long-short-ratio-history", {**base_params, "symbols": perp_symbol})
            data['ls_ratio_history'] = [float(x.get('r', 0)) for x in ls_hist[0]['history']] if ls_hist else []
        except Exception as e:
            print(f"⚠️ Long/Short Ratio error: {e}")
            data['ls_ratio_history'] = []
        
        # OHLCV History for price data
        try:
            ohlcv_hist = self._get("/ohlcv-history", {**base_params, "symbols": perp_symbol})
            if ohlcv_hist:
                history = ohlcv_hist[0]['history']
                data['price_history'] = [float(x['c']) for x in history]  # Close prices
                data['volume_history'] = [float(x['v']) for x in history]  # Volume
                data['current_price'] = data['price_history'][-1] if data['price_history'] else 0
            else:
                data['price_history'] = []
                data['volume_history'] = []
                data['current_price'] = 0
        except Exception as e:
            print(f"⚠️ OHLCV error: {e}")
            data['price_history'] = []
            data['volume_history'] = []
            data['current_price'] = 0
        
        return data
    
    def analyze_crypto(self, symbol: str) -> Dict[str, Any]:
        """Complete analysis of a cryptocurrency using only Coinalyze data"""
        print(f"🔍 Analyzing {symbol.upper()} using Coinalyze API...")
        
        # Find symbols
        try:
            perp_symbol, spot_symbol = self.find_symbol(symbol)
            print(f"📊 Found: {perp_symbol} (perp), {spot_symbol} (spot)")
        except Exception as e:
            raise ValueError(f"Could not find {symbol}: {e}")
        
        # Get current data
        current_data = self.get_current_data(perp_symbol, spot_symbol)
        
        # Get historical data
        historical_data = self.get_historical_data(perp_symbol, spot_symbol)
        
        # Calculate metrics
        metrics = self._calculate_metrics(current_data, historical_data)
        
        # Combine all data
        analysis = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symbol': symbol.upper(),
            'perp_symbol': perp_symbol,
            'spot_symbol': spot_symbol,
            'current_data': current_data,
            'historical_data': historical_data,
            'metrics': metrics
        }
        
        return analysis
    
    def _calculate_metrics(self, current: Dict[str, Any], historical: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from the data"""
        metrics = {}
        
        # Current metrics
        metrics['current_price'] = historical.get('current_price', 0)
        metrics['open_interest_usd'] = current.get('open_interest_usd', 0)
        metrics['funding_rate_pct'] = current.get('funding_rate', 0) * 100
        metrics['predicted_funding_rate_pct'] = current.get('predicted_funding_rate', 0) * 100
        
        # Historical analysis
        if historical.get('price_history'):
            prices = historical['price_history']
            if len(prices) >= 24:
                metrics['price_change_24h_pct'] = ((prices[-1] - prices[-24]) / prices[-24]) * 100
            if len(prices) >= 2:
                metrics['price_change_1h_pct'] = ((prices[-1] - prices[-2]) / prices[-2]) * 100
        
        # Liquidations
        liq_long = historical.get('liquidations_long', [])
        liq_short = historical.get('liquidations_short', [])
        if liq_long and liq_short:
            metrics['liquidations_long_24h_usd'] = sum(liq_long)
            metrics['liquidations_short_24h_usd'] = sum(liq_short)
            metrics['liquidations_ratio'] = sum(liq_long) / max(sum(liq_short), 1)
        
        # Long/Short Ratio
        ls_history = historical.get('ls_ratio_history', [])
        if ls_history:
            metrics['current_ls_ratio'] = ls_history[-1] if ls_history else 0
            metrics['avg_ls_ratio_24h'] = sum(ls_history) / len(ls_history)
        
        # Open Interest trend
        oi_history = historical.get('oi_history', [])
        if oi_history and len(oi_history) >= 2:
            metrics['oi_change_24h_pct'] = ((oi_history[-1] - oi_history[0]) / oi_history[0]) * 100
        
        return metrics
    
    def get_ai_analysis(self, analysis: Dict[str, Any]) -> str:
        """Get AI analysis of the data"""
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            metrics = analysis['metrics']
            symbol = analysis['symbol']
            
            prompt = f"""
            Analyze {symbol} derivatives data and provide a concise trading recommendation.
            
            Current Data:
            - Price: ${metrics.get('current_price', 0):.2f}
            - 24h Change: {metrics.get('price_change_24h_pct', 0):.2f}%
            - Open Interest: ${metrics.get('open_interest_usd', 0):,.0f}
            - OI Change 24h: {metrics.get('oi_change_24h_pct', 0):.2f}%
            - Funding Rate: {metrics.get('funding_rate_pct', 0):.4f}%
            - Predicted Funding: {metrics.get('predicted_funding_rate_pct', 0):.4f}%
            - Long/Short Ratio: {metrics.get('current_ls_ratio', 0):.2f}
            - Liquidations Long/Short: ${metrics.get('liquidations_long_24h_usd', 0):,.0f} / ${metrics.get('liquidations_short_24h_usd', 0):,.0f}
            
            Provide:
            1. Market sentiment (BULLISH/BEARISH/NEUTRAL)
            2. Key insights from derivatives data
            3. Specific trading recommendation with entry/exit levels
            4. Risk assessment
            
            Keep response under 200 words.
            """
            
            try:
                # Try o3-mini first
                response = client.chat.completions.create(
                    model="o3-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=300
                )
            except:
                # Fallback to GPT-4
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=250,
                    temperature=0.2
                )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI analysis unavailable: {e}"


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Clean Coinalyze-only crypto analysis")
    parser.add_argument("--symbol", "-s", default="SOL", help="Crypto symbol to analyze")
    parser.add_argument("--whatsapp", action="store_true", help="Send to WhatsApp")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()
    
    try:
        # Initialize agent
        agent = CoinalyzeCryptoAgent()
        
        # Analyze crypto
        analysis = agent.analyze_crypto(args.symbol)
        
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            # Pretty print analysis
            symbol = analysis['symbol']
            metrics = analysis['metrics']
            
            print(f"\n🚀 {symbol} Analysis (Coinalyze Only)")
            print("=" * 50)
            print(f"💰 Price: ${metrics.get('current_price', 0):.2f}")
            print(f"📈 24h Change: {metrics.get('price_change_24h_pct', 0):+.2f}%")
            print(f"🏦 Open Interest: ${metrics.get('open_interest_usd', 0):,.0f}")
            print(f"📊 OI Change 24h: {metrics.get('oi_change_24h_pct', 0):+.2f}%")
            print(f"💸 Funding Rate: {metrics.get('funding_rate_pct', 0):.4f}%")
            print(f"🔮 Predicted Funding: {metrics.get('predicted_funding_rate_pct', 0):.4f}%")
            print(f"⚖️ Long/Short Ratio: {metrics.get('current_ls_ratio', 0):.2f}")
            print(f"💥 Liquidations L/S: ${metrics.get('liquidations_long_24h_usd', 0):,.0f} / ${metrics.get('liquidations_short_24h_usd', 0):,.0f}")
            
            # Get AI analysis
            print(f"\n🤖 AI Analysis:")
            print("-" * 30)
            ai_analysis = agent.get_ai_analysis(analysis)
            print(ai_analysis)
        
        # WhatsApp integration
        if args.whatsapp:
            try:
                from whatsapp_sender import WhatsAppSender
                
                metrics = analysis['metrics']
                summary = f"""📊 {analysis['symbol']} Analysis
💰 ${metrics.get('current_price', 0):.2f} ({metrics.get('price_change_24h_pct', 0):+.2f}%)
🏦 OI: ${metrics.get('open_interest_usd', 0)/1e6:.1f}M ({metrics.get('oi_change_24h_pct', 0):+.2f}%)
💸 FR: {metrics.get('funding_rate_pct', 0):.4f}%
⚖️ L/S: {metrics.get('current_ls_ratio', 0):.2f}

{ai_analysis[:200]}..."""
                
                sender = WhatsAppSender()
                sender.send_message(summary)
                print("✅ Sent to WhatsApp")
            except ImportError:
                print("❌ WhatsApp sender not available")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())