#!/usr/bin/env python3
"""
Simple Hourly SOL Analysis
==========================
1. Get data snapshot
2. Detect changes/patterns 
3. Analyze with reasoning
4. Send to WhatsApp only if significant changes
5. Track state to avoid duplicates

No complexity, just works.
"""

import os
import time
import json
import requests
from datetime import datetime, timezone
from openai import OpenAI
from whatsapp_sender import WhatsAppSender

class HourlySolAnalysis:
    def __init__(self):
        self.coinalyze_key = os.getenv('COINALYZE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        if not self.coinalyze_key:
            raise ValueError("COINALYZE_API_KEY required")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required")
            
        self.session = requests.Session()
        self.session.headers.update({'api_key': self.coinalyze_key})
        self.perp_symbol = "SOLUSDT_PERP.A"
        
        # State file to track last analysis
        self.state_file = 'sol_analysis_state.json'
    
    def _api_get(self, endpoint, params=None):
        """Safe API call with debug info"""
        try:
            url = f"https://api.coinalyze.net/v1{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ API {endpoint} returned {response.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ API {endpoint} error: {e}")
            return None
    
    def get_current_snapshot(self):
        """Get comprehensive market snapshot"""
        print("📊 Fetching comprehensive SOL data...")
        
        now = int(time.time())
        
        # 1. Current price + 24h history
        current_price = 0
        price_24h_change = 0
        try:
            price_data = self._api_get("/ohlcv-history", {
                "symbols": self.perp_symbol,
                "interval": "1hour", 
                "from": now - (24 * 3600),
                "to": now
            })
            
            if price_data and price_data[0].get('history'):
                history = price_data[0]['history']
                current_price = float(history[-1]['c'])
                if len(history) > 1:
                    price_24h_ago = float(history[0]['c'])
                    price_24h_change = (current_price - price_24h_ago) / price_24h_ago * 100
        except Exception as e:
            print(f"⚠️ Price data error: {e}")
        
        # 2. Open Interest + 24h change
        oi_usd = 0
        oi_24h_change = 0
        try:
            oi_data = self._api_get("/open-interest", {
                "symbols": self.perp_symbol,
                "convert_to_usd": "true"
            })
            oi_usd = float(oi_data[0]['value']) if oi_data else 0
            
            oi_history = self._api_get("/open-interest-history", {
                "symbols": self.perp_symbol,
                "interval": "1hour",
                "from": now - (24 * 3600),
                "to": now,
                "convert_to_usd": "true"
            })
            
            if oi_history and oi_history[0].get('history'):
                history = oi_history[0]['history'] 
                if len(history) > 1:
                    # Try different possible field names for OI value
                    oi_24h_ago = 0
                    first_record = history[0]
                    if 'v' in first_record:
                        oi_24h_ago = float(first_record['v'])
                    elif 'value' in first_record:
                        oi_24h_ago = float(first_record['value'])
                    elif 'oi' in first_record:
                        oi_24h_ago = float(first_record['oi'])
                    
                    if oi_24h_ago > 0:
                        oi_24h_change = (oi_usd - oi_24h_ago) / oi_24h_ago * 100
        except Exception as e:
            print(f"⚠️ Open Interest data error: {e}")
        
        # 3. Funding Rate + predicted
        funding_rate = 0
        predicted_funding_rate = 0
        try:
            funding_data = self._api_get("/funding-rate", {"symbols": self.perp_symbol})
            funding_rate = float(funding_data[0]['value']) * 100 if funding_data else 0
            
            predicted_funding = self._api_get("/predicted-funding-rate", {"symbols": self.perp_symbol})
            predicted_funding_rate = float(predicted_funding[0]['value']) * 100 if predicted_funding else 0
        except Exception as e:
            print(f"⚠️ Funding data error: {e}")
        
        # 4. Long/Short Ratio + 24h patterns
        ls_ratio = 0
        ls_24h_avg = 0
        ls_24h_change = 0
        try:
            ls_data = self._api_get("/long-short-ratio-history", {
                "symbols": self.perp_symbol,
                "interval": "1hour",
                "from": now - (24 * 3600), 
                "to": now
            })
            
            if ls_data and ls_data[0].get('history'):
                history = ls_data[0]['history']
                if history:
                    ls_ratio = float(history[-1].get('r', 0))
                    # Calculate 24h average
                    ratios = [float(h.get('r', 0)) for h in history if h.get('r')]
                    ls_24h_avg = sum(ratios) / len(ratios) if ratios else 0
                    # Calculate 24h change
                    if len(history) > 1:
                        ls_24h_ago = float(history[0].get('r', 0))
                        if ls_24h_ago > 0:
                            ls_24h_change = (ls_ratio - ls_24h_ago) / ls_24h_ago * 100
        except Exception as e:
            print(f"⚠️ Long/Short data error: {e}")
        
        # 5. Comprehensive liquidations (24h)
        long_liq_24h = short_liq_24h = 0
        long_liq_6h = short_liq_6h = 0
        try:
            liq_data = self._api_get("/liquidation-history", {
                "symbols": self.perp_symbol,
                "interval": "1hour", 
                "from": now - (24 * 3600),
                "to": now,
                "convert_to_usd": "true"
            })
            
            if liq_data and liq_data[0].get('history'):
                history = liq_data[0]['history']
                for i, item in enumerate(history):
                    long_val = item.get('l', 0)
                    short_val = item.get('s', 0)
                    long_liq_24h += long_val
                    short_liq_24h += short_val
                    # Last 6 hours
                    if i >= len(history) - 6:
                        long_liq_6h += long_val
                        short_liq_6h += short_val
        except Exception as e:
            print(f"⚠️ Liquidation data error: {e}")
        
        # 6. Basis (perp vs spot spread)
        basis_pct = 0
        try:
            basis_data = self._api_get("/basis", {"symbols": self.perp_symbol})
            basis_pct = float(basis_data[0]['value']) * 100 if basis_data else 0
        except Exception as e:
            print(f"⚠️ Basis data error: {e}")
        
        snapshot = {
            'timestamp': now,
            'price': current_price,
            'price_24h_change': price_24h_change,
            'oi_usd': oi_usd,
            'oi_24h_change': oi_24h_change,
            'funding_pct': funding_rate,
            'predicted_funding_pct': predicted_funding_rate,
            'ls_ratio': ls_ratio,
            'ls_24h_avg': ls_24h_avg,
            'ls_24h_change': ls_24h_change,
            'long_liq_24h': long_liq_24h,
            'short_liq_24h': short_liq_24h,
            'long_liq_6h': long_liq_6h,
            'short_liq_6h': short_liq_6h,
            'basis_pct': basis_pct
        }
        
        print(f"   💰 Price: ${current_price:.2f} ({price_24h_change:+.1f}% 24h)")
        print(f"   🏦 OI: ${oi_usd/1e6:.1f}M ({oi_24h_change:+.1f}% 24h)")
        print(f"   💸 Funding: {funding_rate:.3f}% (pred: {predicted_funding_rate:.3f}%)")
        print(f"   ⚖️ L/S: {ls_ratio:.2f} (24h avg: {ls_24h_avg:.2f}, {ls_24h_change:+.1f}%)")
        print(f"   🔥 Liq 24h: ${long_liq_24h/1e6:.1f}M L / ${short_liq_24h/1e6:.1f}M S")
        print(f"   📈 Basis: {basis_pct:.3f}%")
        
        return snapshot
    
    def load_last_state(self):
        """Load last analysis state"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def save_state(self, data):
        """Save current state"""
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def should_send_alert(self, current, last):
        """Determine if changes are significant enough to send alert"""
        if not last:
            return True, "First analysis"
        
        # Check for significant changes
        price_change = abs(current['price'] - last['price']) / last['price'] * 100
        oi_change = abs(current['oi_usd'] - last['oi_usd']) / last['oi_usd'] * 100
        funding_change = abs(current['funding_pct'] - last['funding_pct'])
        ls_change = abs(current['ls_ratio'] - last['ls_ratio']) / last['ls_ratio'] * 100
        
        # Check 24h price momentum shift
        price_momentum_change = 0
        if 'price_24h_change' in last:
            price_momentum_change = abs(current['price_24h_change'] - last['price_24h_change'])
        
        # Thresholds for significant changes
        if price_change > 2.0:
            return True, f"Price moved {price_change:.1f}%"
        if oi_change > 5.0:
            return True, f"OI changed {oi_change:.1f}%"
        if funding_change > 0.05:
            return True, f"Funding shifted {funding_change:.3f}%"
        if ls_change > 10.0:
            return True, f"L/S changed {ls_change:.1f}%"
        
        # New thresholds for comprehensive data
        if price_momentum_change > 3.0:
            return True, f"24h momentum shift {price_momentum_change:.1f}%"
        if abs(current['oi_24h_change']) > 8.0:
            return True, f"OI 24h change {abs(current['oi_24h_change']):.1f}%"
        if abs(current['ls_24h_change']) > 15.0:
            return True, f"L/S 24h change {abs(current['ls_24h_change']):.1f}%"
            
        # Check liquidation spikes
        total_liq_6h = current['long_liq_6h'] + current['short_liq_6h']
        if total_liq_6h > 5e6:  # $5M+ in 6h liquidations
            return True, f"High liquidations ${total_liq_6h/1e6:.1f}M in 6h"
            
        # Check time since last alert (max 4 hours)
        hours_since = (current['timestamp'] - last['timestamp']) / 3600
        if hours_since > 4:
            return True, f"4+ hours since last update"
        
        return False, "No significant changes"
    
    def analyze_with_reasoning(self, current, last=None):
        """Generate comprehensive analysis with reasoning"""
        client = OpenAI(api_key=self.openai_key)
        
        # Calculate changes if we have previous data
        changes = ""
        if last:
            price_chg = (current['price'] - last['price']) / last['price'] * 100
            oi_chg = (current['oi_usd'] - last['oi_usd']) / last['oi_usd'] * 100
            funding_chg = current['funding_pct'] - last['funding_pct']
            ls_chg = (current['ls_ratio'] - last['ls_ratio']) / last['ls_ratio'] * 100
            
            changes = f"""
CHANGES SINCE LAST ANALYSIS:
• Price: {price_chg:+.1f}%
• OI: {oi_chg:+.1f}%  
• Funding: {funding_chg:+.3f}%
• L/S Ratio: {ls_chg:+.1f}%
"""
        
        prompt = f"""
Analyze comprehensive SOL derivatives data and provide trading insights with reasoning:

COMPREHENSIVE MARKET DATA:
• Price: ${current['price']:.2f} ({current['price_24h_change']:+.1f}% 24h)
• Open Interest: ${current['oi_usd']/1e6:.1f}M ({current['oi_24h_change']:+.1f}% 24h)
• Funding Rate: {current['funding_pct']:.3f}% (predicted: {current['predicted_funding_pct']:.3f}%)
• Long/Short Ratio: {current['ls_ratio']:.2f} (24h avg: {current['ls_24h_avg']:.2f}, change: {current['ls_24h_change']:+.1f}%)
• Liquidations 24h: Long ${current['long_liq_24h']/1e6:.1f}M | Short ${current['short_liq_24h']/1e6:.1f}M
• Liquidations 6h: Long ${current['long_liq_6h']/1e6:.1f}M | Short ${current['short_liq_6h']/1e6:.1f}M  
• Basis (perp-spot): {current['basis_pct']:.3f}%
{changes}

CRITICAL ANALYSIS REQUIREMENTS:
- Identify key patterns and correlations between metrics
- Explain the logic behind funding vs L/S positioning dynamics
- Note any divergences between price action and positioning
- Consider liquidation patterns and basis effects
- Provide actionable insights with reasoning

Provide analysis in this exact format:

🎯 BIAS: [BULLISH/BEARISH/NEUTRAL/UNCLEAR]
📊 KEY INSIGHT: [Explain the main pattern/correlation driving this view. Be specific about the logic connecting funding, L/S, OI changes, liquidations]
⚠️ TOP RISK: [Key risk scenario with specific price levels based on positioning data]
💡 ACTION: [Specific trading recommendation with entry/exit levels and reasoning]

Keep under 480 characters total for WhatsApp compatibility.
"""
        
        try:
            print("🧠 Calling o3 model for analysis...")
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an elite derivatives trading analyst. Provide concise but insightful analysis with clear reasoning showing how you connect different market metrics."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=800
            )
            
            analysis = response.choices[0].message.content.strip()
            print(f"✅ o3 analysis received ({len(analysis)} chars)")
            return analysis
            
        except Exception as e:
            print(f"❌ o3 model failed: {e}")
            print("🔄 Using enhanced fallback analysis...")
            
            # Enhanced fallback with comprehensive data
            if current['funding_pct'] < -0.15 and current['ls_ratio'] > 2.8:
                bias = "BEARISH" 
                insight = f"L/S {current['ls_ratio']:.1f} vs funding {current['funding_pct']:.2f}% shows retail crowded long while smart money shorts. Basis {current['basis_pct']:.2f}% confirms perp discount."
                risk = f"Long liquidations above ${current['long_liq_24h']/1e6:.0f}M could cascade if price breaks support"
                action = "Short rallies above current price, target breakdown levels"
            elif current['funding_pct'] > 0.1 and current['ls_ratio'] < 1.5:
                bias = "BULLISH"
                insight = f"Low L/S {current['ls_ratio']:.1f} with positive funding {current['funding_pct']:.2f}% shows shorts squeezed. OI {current['oi_24h_change']:+.1f}% suggests fresh positioning."
                risk = f"Short squeeze risk if price breaks resistance"
                action = "Long dips, target squeeze levels above current highs"
            else:
                bias = "UNCLEAR"
                insight = f"Mixed signals: L/S {current['ls_ratio']:.1f}, funding {current['funding_pct']:.2f}%, OI {current['oi_24h_change']:+.1f}% show conflicting forces"
                risk = "Range-bound action with low conviction until clearer pattern emerges"
                action = "Wait for breakout confirmation or positioning extremes"
            
            return f"""🎯 BIAS: {bias}
📊 KEY INSIGHT: {insight}
⚠️ TOP RISK: {risk}
💡 ACTION: {action}"""
    
    def format_whatsapp(self, analysis, data):
        """Format for WhatsApp with rich header"""
        utc_time = datetime.now(timezone.utc).strftime('%H:%M UTC')
        
        header = f"🎯 SOL • {utc_time}\n"
        header += f"📊 ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h) | OI: ${data['oi_usd']/1e6:.1f}M ({data['oi_24h_change']:+.1f}%)\n"
        header += f"💸 {data['funding_pct']:.3f}% → {data['predicted_funding_pct']:.3f}% | L/S: {data['ls_ratio']:.2f}\n\n"
        
        return header + analysis + "\n\n📈 Hourly + o3"
    
    def run_hourly_analysis(self):
        """Main hourly analysis workflow"""
        print("🚀 SOL Hourly Analysis Starting...")
        
        try:
            # 1. Get current snapshot
            current = self.get_current_snapshot()
            
            # 2. Load last state
            last_state = self.load_last_state()
            
            # 3. Check if we should send alert
            should_send, reason = self.should_send_alert(current, last_state)
            
            print(f"📊 Should send alert: {should_send} - {reason}")
            
            if not should_send:
                print("✅ No significant changes, skipping alert")
                return
            
            # 4. Analyze with reasoning
            print("🧠 Generating analysis...")
            analysis = self.analyze_with_reasoning(current, last_state)
            
            # 5. Format for WhatsApp
            whatsapp_msg = self.format_whatsapp(analysis, current)
            
            print(f"📱 WhatsApp message ({len(whatsapp_msg)} chars):")
            print("-" * 40)
            print(whatsapp_msg)
            print("-" * 40)
            
            # 6. Send to WhatsApp
            if os.getenv('AUTO_SEND_TO_WHATSAPP', 'true').lower() == 'true':
                sender = WhatsAppSender()
                success = sender.send_message(whatsapp_msg)
                if success:
                    print("✅ WhatsApp sent successfully")
                    # 7. Save state only after successful send
                    current['last_analysis'] = analysis
                    current['last_whatsapp'] = whatsapp_msg
                    self.save_state(current)
                else:
                    print("❌ WhatsApp send failed")
            else:
                print("📱 AUTO_SEND_TO_WHATSAPP disabled")
                # Save state anyway for testing
                current['last_analysis'] = analysis
                self.save_state(current)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            print("🔍 Full error traceback:")
            traceback.print_exc()


def main():
    """Simple main function"""
    analysis = HourlySolAnalysis()
    analysis.run_hourly_analysis()
    print("✅ Hourly analysis complete!")


if __name__ == "__main__":
    main()