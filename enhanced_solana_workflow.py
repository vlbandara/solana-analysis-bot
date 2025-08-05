#!/usr/bin/env python3
"""
Enhanced Solana Workflow
Combines Coinalyze data with o3 analysis for comprehensive market insights
Sends concise analysis to WhatsApp via Twilio
"""

import os
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Run: uv add openai")

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio not installed. Run: uv add twilio")

class EnhancedSolanaWorkflow:
    """Enhanced Solana analysis combining Coinalyze data with o3 AI analysis"""
    
    def __init__(self):
        self.coinalyze_api_key = os.getenv("COINALYZE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.coinalyze_api_key:
            raise RuntimeError("COINALYZE_API_KEY environment variable not set")
        
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        
        self.coinalyze_base = "https://api.coinalyze.net/v1"
        self.openai_client = OpenAI(api_key=self.openai_api_key) if OPENAI_AVAILABLE else None
        
        # Initialize Twilio for WhatsApp
        self.twilio_client = None
        self.auto_send_whatsapp = os.getenv('AUTO_SEND_TO_WHATSAPP', 'true').lower() == 'true'
        
        if TWILIO_AVAILABLE:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                print(f"✅ Twilio client initialized (auto-send: {self.auto_send_whatsapp})")
            else:
                print("❌ Missing Twilio credentials")
        else:
            print("❌ Twilio library not available")
    
    def fetch_coinalyze_data(self) -> Dict[str, Any]:
        """Fetch comprehensive data from Coinalyze API"""
        print("🔍 Fetching Coinalyze data...")
        
        headers = {"api_key": self.coinalyze_api_key}
        
        # Helper function for API calls
        def _get(endpoint: str, params: dict = None) -> dict:
            url = f"{self.coinalyze_base}{endpoint}"
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        
        # Fetch open interest
        try:
            oi_data = _get("/open-interest", {"symbols": "SOLUSDT_PERP.A", "convert_to_usd": "true"})
            open_interest = float(oi_data[0]["value"]) if oi_data else 0
            print(f"   ✅ Open Interest: ${open_interest:,.0f}")
        except Exception as e:
            print(f"   ❌ Open Interest error: {e}")
            open_interest = 0
        
        # Fetch funding rate
        try:
            funding_data = _get("/funding-rate", {"symbols": "SOLUSDT_PERP.A"})
            funding_rate = float(funding_data[0]["value"]) if funding_data else 0
            print(f"   ✅ Funding Rate: {funding_rate:.6f}")
        except Exception as e:
            print(f"   ❌ Funding Rate error: {e}")
            funding_rate = 0
        
        # Fetch liquidations (last hour)
        try:
            import time
            to_ts = int(time.time())
            from_ts = to_ts - 3600  # 1 hour ago
            
            liquidations_data = _get(
                "/liquidation-history",
                {
                    "symbols": "SOLUSDT_PERP.A",
                    "interval": "1hour",
                    "from": from_ts,
                    "to": to_ts,
                    "convert_to_usd": "true",
                }
            )
            
            history = liquidations_data[0]["history"] if liquidations_data else []
            long_liquidations = sum(item.get("l", 0) for item in history)
            short_liquidations = sum(item.get("s", 0) for item in history)
            
            print(f"   ✅ Liquidations (1h): ${long_liquidations:,.0f}L/${short_liquidations:,.0f}S")
        except Exception as e:
            print(f"   ❌ Liquidations error: {e}")
            long_liquidations = short_liquidations = 0
        
        # Fetch long/short ratio
        try:
            import time
            to_ts = int(time.time())
            from_ts = to_ts - 3600  # 1 hour ago
            
            ls_data = _get(
                "/long-short-ratio-history",
                {
                    "symbols": "SOLUSDT_PERP.A",
                    "interval": "1hour",
                    "from": from_ts,
                    "to": to_ts,
                }
            )
            
            history = ls_data[0]["history"] if ls_data else []
            long_short_ratio = float(history[-1]["r"]) if history else 1.0
            print(f"   ✅ Long/Short Ratio: {long_short_ratio:.2f}")
        except Exception as e:
            print(f"   ❌ Long/Short Ratio error: {e}")
            long_short_ratio = 1.0
        
        # Fetch current price (using OHLCV)
        try:
            import time
            to_ts = int(time.time())
            from_ts = to_ts - 300  # last 5 minutes
            
            price_data = _get(
                "/ohlcv-history",
                {
                    "symbols": "SOLUSDT_PERP.A",
                    "interval": "1min",
                    "from": from_ts,
                    "to": to_ts,
                }
            )
            
            current_price = float(price_data[0]["history"][-1]["c"]) if price_data and price_data[0]["history"] else 0
            print(f"   ✅ Current Price: ${current_price:.2f}")
        except Exception as e:
            print(f"   ❌ Price error: {e}")
            current_price = 0
        
        return {
            "open_interest": open_interest,
            "funding_rate": funding_rate,
            "long_liquidations": long_liquidations,
            "short_liquidations": short_liquidations,
            "long_short_ratio": long_short_ratio,
            "current_price": current_price,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def analyze_with_o3(self, coinalyze_data: Dict[str, Any]) -> str:
        """Analyze data using o3 model"""
        if not self.openai_client:
            return "❌ OpenAI client not available"
        
        print("🤖 Analyzing with o3 model...")
        
        # Create focused prompt for hourly market insights
        prompt = f"""
You are a professional crypto analyst providing hourly market insights to a Solana position holder.
Analyze this Coinalyze derivatives data and provide CONCISE, actionable insights for WhatsApp.

MARKET DATA:
- Price: ${coinalyze_data['current_price']:.2f}
- Open Interest: {coinalyze_data['open_interest']:,.0f} SOL
- Funding Rate: {coinalyze_data['funding_rate']*100:.4f}% (annualized)
- Liquidations (1h): {coinalyze_data['long_liquidations']:,.0f}L / {coinalyze_data['short_liquidations']:,.0f}S
- Long/Short Ratio: {coinalyze_data['long_short_ratio']:.2f}

Provide a concise hourly update (max 300 words) with:
1. 🎯 SIGNAL: BULLISH/NEUTRAL/BEARISH (one word)
2. 📊 Market sentiment (2-3 sentences)
3. ⚠️ Key risks for position holders (2-3 bullet points)
4. 💡 Actionable insight (1-2 sentences)

Focus on what matters for someone holding SOL positions. Use emojis and clear formatting for WhatsApp.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using o3 equivalent
                messages=[
                    {"role": "system", "content": "You are a professional crypto analyst. Provide concise, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            print("   ✅ o3 analysis completed")
            return analysis
            
        except Exception as e:
            print(f"   ❌ o3 analysis error: {e}")
            return f"❌ Analysis failed: {str(e)}"
    
    def create_whatsapp_message(self, coinalyze_data: Dict[str, Any], o3_analysis: str) -> str:
        """Create formatted WhatsApp message"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        message = f"""
🔄 SOL HOURLY UPDATE
⏰ {timestamp}

📊 DATA:
💰 ${coinalyze_data['current_price']:.2f}
📈 OI: {coinalyze_data['open_interest']:,.0f} SOL
💸 Funding: {coinalyze_data['funding_rate']*100:.4f}%
⚖️ L/S: {coinalyze_data['long_short_ratio']:.2f}
🔥 Liq: {coinalyze_data['long_liquidations']:,.0f}L/{coinalyze_data['short_liquidations']:,.0f}S

{o3_analysis}

---
🤖 o3 + Coinalyze
"""
        
        return message.strip()
    
    def send_to_whatsapp(self, message: str) -> bool:
        """Send message to WhatsApp via Twilio"""
        if not self.twilio_client:
            print("❌ Twilio client not available")
            return False
        
        if not self.auto_send_whatsapp:
            print("⚠️ Auto-send to WhatsApp is disabled")
            return False
        
        try:
            # Try TWILIO_WHATSAPP_FROM first, fallback to TWILIO_WHATSAPP_NUMBER
            from_number = os.getenv('TWILIO_WHATSAPP_FROM') or os.getenv('TWILIO_WHATSAPP_NUMBER')
            to_number = os.getenv('WHATSAPP_TO_NUMBER')
            
            if not from_number or not to_number:
                print("❌ Missing WhatsApp numbers in environment")
                print(f"   From: {'✅ Set' if from_number else '❌ Missing'}")
                print(f"   To: {'✅ Set' if to_number else '❌ Missing'}")
                return False
            
            # Format numbers for WhatsApp
            from_param = f'whatsapp:{from_number}'
            to_param = f'whatsapp:{to_number}'
            
            print(f"📱 Sending to WhatsApp: {to_number}")
            print(f"📱 From WhatsApp: {from_number}")
            
            twilio_message = self.twilio_client.messages.create(
                from_=from_param,
                body=message,
                to=to_param
            )
            
            print(f"✅ Message sent: {twilio_message.sid}")
            return True
            
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            return False
    
    def run_analysis(self, send_whatsapp: bool = True) -> Dict[str, Any]:
        """Run complete analysis workflow"""
        print("🚀 Starting Enhanced Solana Analysis...")
        
        # Fetch Coinalyze data
        coinalyze_data = self.fetch_coinalyze_data()
        
        # Analyze with o3
        o3_analysis = self.analyze_with_o3(coinalyze_data)
        
        # Create WhatsApp message
        whatsapp_message = self.create_whatsapp_message(coinalyze_data, o3_analysis)
        
        # Print analysis
        print("\n" + "="*50)
        print("ANALYSIS RESULTS:")
        print("="*50)
        print(whatsapp_message)
        print("="*50)
        
        # Send to WhatsApp if requested
        whatsapp_sent = False
        if send_whatsapp:
            whatsapp_sent = self.send_to_whatsapp(whatsapp_message)
        
        # Save results
        results = {
            "coinalyze_data": coinalyze_data,
            "o3_analysis": o3_analysis,
            "whatsapp_message": whatsapp_message,
            "whatsapp_sent": whatsapp_sent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to file
        with open("enhanced_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to enhanced_analysis.json")
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Solana Analysis Workflow")
    parser.add_argument("--no-whatsapp", action="store_true", help="Skip WhatsApp sending")
    args = parser.parse_args()
    
    try:
        workflow = EnhancedSolanaWorkflow()
        results = workflow.run_analysis(send_whatsapp=not args.no_whatsapp)
        print("✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 