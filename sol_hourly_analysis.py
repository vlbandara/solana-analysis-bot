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
        """Safe API call"""
        try:
            url = f"https://api.coinalyze.net/v1{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_current_snapshot(self):
        """Get current market snapshot"""
        print("📊 Fetching SOL data snapshot...")
        
        now = int(time.time())
        
        # Current price
        price_data = self._api_get("/ohlcv-history", {
            "symbols": self.perp_symbol,
            "interval": "1min",
            "from": now - 300,
            "to": now
        })
        
        current_price = 0
        if price_data and price_data[0].get('history'):
            current_price = float(price_data[0]['history'][-1]['c'])
        
        # Open Interest
        oi_data = self._api_get("/open-interest", {
            "symbols": self.perp_symbol,
            "convert_to_usd": "true"
        })
        oi_usd = float(oi_data[0]['value']) if oi_data else 0
        
        # Funding Rate
        funding_data = self._api_get("/funding-rate", {"symbols": self.perp_symbol})
        funding_rate = float(funding_data[0]['value']) * 100 if funding_data else 0
        
        # Long/Short Ratio
        ls_data = self._api_get("/long-short-ratio-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour",
            "from": now - 3600,
            "to": now
        })
        
        ls_ratio = 0
        if ls_data and ls_data[0].get('history'):
            latest = ls_data[0]['history'][-1]
            ls_ratio = float(latest.get('r', 0))
        
        # Recent liquidations (6h)
        liq_data = self._api_get("/liquidation-history", {
            "symbols": self.perp_symbol,
            "interval": "1hour", 
            "from": now - (6 * 3600),
            "to": now,
            "convert_to_usd": "true"
        })
        
        long_liq = short_liq = 0
        if liq_data and liq_data[0].get('history'):
            for item in liq_data[0]['history']:
                long_liq += item.get('l', 0)
                short_liq += item.get('s', 0)
        
        snapshot = {
            'timestamp': now,
            'price': current_price,
            'oi_usd': oi_usd,
            'funding_pct': funding_rate,
            'ls_ratio': ls_ratio,
            'long_liq_6h': long_liq,
            'short_liq_6h': short_liq
        }
        
        print(f"   Price: ${current_price:.2f}")
        print(f"   OI: ${oi_usd/1e6:.1f}M")
        print(f"   Funding: {funding_rate:.3f}%") 
        print(f"   L/S: {ls_ratio:.2f}")
        
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
        
        # Thresholds for significant changes
        if price_change > 2.0:
            return True, f"Price moved {price_change:.1f}%"
        if oi_change > 5.0:
            return True, f"OI changed {oi_change:.1f}%"
        if funding_change > 0.05:
            return True, f"Funding shifted {funding_change:.3f}%"
        if ls_change > 10.0:
            return True, f"L/S changed {ls_change:.1f}%"
            
        # Check time since last alert (max 4 hours)
        hours_since = (current['timestamp'] - last['timestamp']) / 3600
        if hours_since > 4:
            return True, f"4+ hours since last update"
        
        return False, "No significant changes"
    
    def analyze_with_reasoning(self, current, last=None):
        """Generate analysis with reasoning"""
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
Analyze SOL derivatives snapshot and provide reasoning:

CURRENT DATA:
• Price: ${current['price']:.2f}
• Open Interest: ${current['oi_usd']/1e6:.1f}M
• Funding Rate: {current['funding_pct']:.3f}%
• Long/Short Ratio: {current['ls_ratio']:.2f}
• Liquidations 6h: Long ${current['long_liq_6h']/1e6:.1f}M | Short ${current['short_liq_6h']/1e6:.1f}M
{changes}

Provide analysis in this format:

🎯 BIAS: [BULLISH/BEARISH/NEUTRAL/UNCLEAR]
📊 KEY INSIGHT: [What pattern/correlation explains this bias? Be specific about the logic]
⚠️ TOP RISK: [Key risk with price level based on positioning]
💡 ACTION: [Trading recommendation with reasoning]

Requirements:
• Explain WHY this bias based on funding/L/S correlation
• Keep under 500 characters total
• Show logical reasoning behind conclusions
• If no clear pattern, state UNCLEAR and explain why
"""
        
        try:
            response = client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert derivatives analyst. Explain your reasoning concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=600
            )
            return response.choices[0].message.content
        except:
            # Simple fallback logic
            if current['funding_pct'] < -0.15 and current['ls_ratio'] > 2.5:
                return """🎯 BIAS: BEARISH
📊 KEY INSIGHT: High L/S ratio with negative funding shows retail longs crowded while institutions short
⚠️ TOP RISK: Long cascade below $160 as funding costs squeeze overleveraged positions  
💡 ACTION: Wait for breakdown or short bounces above $170"""
            else:
                return """🎯 BIAS: UNCLEAR
📊 KEY INSIGHT: Mixed signals in positioning data require more clarity
⚠️ TOP RISK: Range-bound consolidation with low conviction
💡 ACTION: Wait for clearer directional signals before positioning"""
    
    def format_whatsapp(self, analysis, data):
        """Format for WhatsApp"""
        utc_time = datetime.now(timezone.utc).strftime('%H:%M UTC')
        
        header = f"🎯 SOL • {utc_time}\n"
        header += f"📊 ${data['price']:.2f} | OI: ${data['oi_usd']/1e6:.1f}M\n"
        header += f"💸 {data['funding_pct']:.3f}% | L/S: {data['ls_ratio']:.2f}\n\n"
        
        return header + analysis + "\n\n📈 Hourly"
    
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


def main():
    """Simple main function"""
    analysis = HourlySolAnalysis()
    analysis.run_hourly_analysis()
    print("✅ Hourly analysis complete!")


if __name__ == "__main__":
    main()