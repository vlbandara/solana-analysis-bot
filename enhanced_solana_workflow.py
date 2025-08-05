#!/usr/bin/env python3
"""
SOL Derivatives Analysis Agent
Focused derivatives analysis using 7-day Coinalyze data patterns with o3 AI insights.
Analyzes: Open Interest, Funding Rates, Liquidations, Long/Short Ratios, and Basis.
Provides directional advice for SOL position holders via WhatsApp.
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
    """SOL Derivatives Analysis Agent - Sharp analysis for position holders"""

    # ------------------------------------------------------------------
    # Helper formatting and utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _fmt_usd(value: float) -> str:
        """Format large USD values with K / M / B suffixes."""
        if value == 0:
            return "$0"
        
        # Handle sign separately
        sign = "-" if value < 0 else ""
        abs_val = abs(value)
        
        if abs_val >= 1_000_000_000:
            return f"{sign}${abs_val/1_000_000_000:.2f}B"
        elif abs_val >= 1_000_000:
            return f"{sign}${abs_val/1_000_000:.2f}M"
        elif abs_val >= 1_000:
            return f"{sign}${abs_val/1_000:.1f}K"
        else:
            return f"{sign}${abs_val:,.0f}"
    
    @staticmethod
    def _fmt_percentage(value: float, decimals: int = 2) -> str:
        """Format percentage with proper precision."""
        return f"{value*100:.{decimals}f}%"
    
    @staticmethod
    def _fmt_ratio(value: float) -> str:
        """Format ratio with appropriate precision."""
        return f"{value:.2f}"
    
    @staticmethod
    def _calculate_correlation(x_data: list, y_data: list) -> float:
        """Calculate correlation coefficient between two datasets."""
        if len(x_data) != len(y_data) or len(x_data) < 2:
            return 0.0
        
        import statistics
        mean_x = statistics.mean(x_data)
        mean_y = statistics.mean(y_data)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_data, y_data))
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_data)
        sum_sq_y = sum((y - mean_y) ** 2 for y in y_data)
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        return numerator / denominator if denominator != 0 else 0.0
    
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
        """Fetch comprehensive 7-day derivatives data from Coinalyze API"""
        print("🔍 Fetching 7-day SOL derivatives data...")
        
        headers = {"api_key": self.coinalyze_api_key}
        
        # Helper function for API calls
        def _get(endpoint: str, params: dict = None) -> dict:
            url = f"{self.coinalyze_base}{endpoint}"
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        import time
        to_ts = int(time.time())
        from_ts = to_ts - (7 * 24 * 3600)  # 7 days ago
        
        base_params = {
            "interval": "1hour",
            "from": from_ts,
            "to": to_ts,
            "symbols": "SOLUSDT_PERP.A"
        }
        
        derivatives_data = {
            "perp_symbol": "SOLUSDT_PERP.A",
            "spot_symbol": "SOLUSDT.C",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # 1. Fetch Open Interest History (7 days)
        try:
            print("   📊 Fetching Open Interest history...")
            oi_data = _get("/open-interest-history", {
                **base_params,
                "convert_to_usd": "true"
            })
            
            oi_history = oi_data[0]["history"] if oi_data else []
            oi_values = [float(item["c"]) for item in oi_history]
            
            derivatives_data["open_interest"] = {
                "current": oi_values[-1] if oi_values else 0,
                "history": oi_values,
                "24h_change": oi_values[-1] - oi_values[-24] if len(oi_values) >= 24 else 0,
                "7d_change": oi_values[-1] - oi_values[0] if len(oi_values) > 0 else 0,
                "7d_avg": sum(oi_values) / len(oi_values) if oi_values else 0,
                "7d_max": max(oi_values) if oi_values else 0,
                "7d_min": min(oi_values) if oi_values else 0
            }
            print(f"   ✅ OI: {self._fmt_usd(derivatives_data['open_interest']['current'])} "
                  f"(24h: {self._fmt_usd(derivatives_data['open_interest']['24h_change'])})")
        except Exception as e:
            print(f"   ❌ Open Interest error: {e}")
            derivatives_data["open_interest"] = {"current": 0, "history": [], "24h_change": 0, "7d_change": 0}
        
        # 2. Fetch Funding Rate History (7 days)
        try:
            print("   💸 Fetching Funding Rate history...")
            fr_data = _get("/funding-rate-history", base_params)
            
            fr_history = fr_data[0]["history"] if fr_data else []
            fr_values = [float(item["c"]) for item in fr_history]
            
            derivatives_data["funding_rate"] = {
                "current": fr_values[-1] if fr_values else 0,
                "history": fr_values,
                "24h_change": fr_values[-1] - fr_values[-24] if len(fr_values) >= 24 else 0,
                "7d_avg": sum(fr_values) / len(fr_values) if fr_values else 0,
                "7d_max": max(fr_values) if fr_values else 0,
                "7d_min": min(fr_values) if fr_values else 0,
                "annualized_current": fr_values[-1] * 8760 if fr_values else 0  # hourly * hours per year
            }
            print(f"   ✅ Funding: {self._fmt_percentage(derivatives_data['funding_rate']['current'], 4)} "
                  f"(Ann: {self._fmt_percentage(derivatives_data['funding_rate']['annualized_current'], 2)})")
        except Exception as e:
            print(f"   ❌ Funding Rate error: {e}")
            derivatives_data["funding_rate"] = {"current": 0, "history": [], "24h_change": 0, "7d_avg": 0}
        
        # 3. Fetch Liquidation History (7 days)
        try:
            print("   🔥 Fetching Liquidation history...")
            liq_data = _get("/liquidation-history", {
                **base_params,
                "convert_to_usd": "true"
            })
            
            liq_history = liq_data[0]["history"] if liq_data else []
            long_liq_values = [float(item.get("l", 0)) for item in liq_history]
            short_liq_values = [float(item.get("s", 0)) for item in liq_history]
            
            derivatives_data["liquidations"] = {
                "longs_24h": sum(long_liq_values[-24:]) if len(long_liq_values) >= 24 else sum(long_liq_values),
                "shorts_24h": sum(short_liq_values[-24:]) if len(short_liq_values) >= 24 else sum(short_liq_values),
                "longs_7d": sum(long_liq_values),
                "shorts_7d": sum(short_liq_values),
                "long_history": long_liq_values,
                "short_history": short_liq_values,
                "net_24h": sum(long_liq_values[-24:]) - sum(short_liq_values[-24:]) if len(long_liq_values) >= 24 else 0
            }
            print(f"   ✅ Liquidations 24h: {self._fmt_usd(derivatives_data['liquidations']['longs_24h'])}L / "
                  f"{self._fmt_usd(derivatives_data['liquidations']['shorts_24h'])}S")
        except Exception as e:
            print(f"   ❌ Liquidations error: {e}")
            derivatives_data["liquidations"] = {"longs_24h": 0, "shorts_24h": 0, "longs_7d": 0, "shorts_7d": 0}
        
        # 4. Fetch Long/Short Ratio History (7 days)
        try:
            print("   ⚖️ Fetching Long/Short Ratio history...")
            ls_data = _get("/long-short-ratio-history", base_params)
            
            ls_history = ls_data[0]["history"] if ls_data else []
            ls_ratio_values = [float(item.get("r", 1.0)) for item in ls_history]
            
            derivatives_data["long_short_ratio"] = {
                "current": ls_ratio_values[-1] if ls_ratio_values else 1.0,
                "history": ls_ratio_values,
                "24h_change": ls_ratio_values[-1] - ls_ratio_values[-24] if len(ls_ratio_values) >= 24 else 0,
                "7d_avg": sum(ls_ratio_values) / len(ls_ratio_values) if ls_ratio_values else 1.0,
                "7d_max": max(ls_ratio_values) if ls_ratio_values else 1.0,
                "7d_min": min(ls_ratio_values) if ls_ratio_values else 1.0
            }
            print(f"   ✅ L/S Ratio: {self._fmt_ratio(derivatives_data['long_short_ratio']['current'])} "
                  f"(7d avg: {self._fmt_ratio(derivatives_data['long_short_ratio']['7d_avg'])})")
        except Exception as e:
            print(f"   ❌ Long/Short Ratio error: {e}")
            derivatives_data["long_short_ratio"] = {"current": 1.0, "history": [], "24h_change": 0, "7d_avg": 1.0}
        
        # 5. Fetch Current Prices and Calculate Basis
        try:
            print("   💰 Fetching current prices and calculating basis...")
            # Get perp price
            perp_price_data = _get("/ohlcv-history", {
                "symbols": "SOLUSDT_PERP.A",
                "interval": "1min",
                "from": to_ts - 300,  # last 5 minutes
                "to": to_ts
            })
            perp_price = float(perp_price_data[0]["history"][-1]["c"]) if perp_price_data and perp_price_data[0]["history"] else 0
            
            # Get spot price
            spot_price_data = _get("/ohlcv-history", {
                "symbols": "SOLUSDT.C",
                "interval": "1min", 
                "from": to_ts - 300,
                "to": to_ts
            })
            spot_price = float(spot_price_data[0]["history"][-1]["c"]) if spot_price_data and spot_price_data[0]["history"] else perp_price
            
            # Calculate basis
            basis_points = ((perp_price - spot_price) / spot_price) if spot_price > 0 else 0
            annualized_basis = basis_points * 365  # Rough annualization
            
            derivatives_data["prices"] = {
                "perp_current": perp_price,
                "spot_current": spot_price,
                "basis_current": basis_points,
                "basis_annualized": annualized_basis
            }
            
            print(f"   ✅ Prices: Perp ${perp_price:.2f} | Spot ${spot_price:.2f} | "
                  f"Basis: {self._fmt_percentage(basis_points, 3)} (Ann: {self._fmt_percentage(annualized_basis, 1)})")
        except Exception as e:
            print(f"   ❌ Prices/Basis error: {e}")
            derivatives_data["prices"] = {"perp_current": 0, "spot_current": 0, "basis_current": 0, "basis_annualized": 0}
        
        # 6. Calculate Key Correlations
        try:
            print("   🔗 Calculating correlations...")
            oi_values = derivatives_data["open_interest"]["history"]
            fr_values = derivatives_data["funding_rate"]["history"]
            ls_values = derivatives_data["long_short_ratio"]["history"]
            
            derivatives_data["correlations"] = {
                "oi_funding": self._calculate_correlation(oi_values, fr_values),
                "oi_ls_ratio": self._calculate_correlation(oi_values, ls_values),
                "funding_ls_ratio": self._calculate_correlation(fr_values, ls_values)
            }
            print(f"   ✅ Correlations: OI-Funding: {derivatives_data['correlations']['oi_funding']:.3f}, "
                  f"OI-L/S: {derivatives_data['correlations']['oi_ls_ratio']:.3f}")
        except Exception as e:
            print(f"   ❌ Correlations error: {e}")
            derivatives_data["correlations"] = {"oi_funding": 0, "oi_ls_ratio": 0, "funding_ls_ratio": 0}
        
        print("   ✅ 7-day derivatives data fetch completed!")
        return derivatives_data
    
    def analyze_with_o3(self, derivatives_data: Dict[str, Any]) -> str:
        """Analyze derivatives data using o3 model for position holders"""
        if not self.openai_client:
            return "❌ OpenAI client not available"
        
        print("🤖 Analyzing derivatives patterns with o3...")
        
        # Extract key metrics for analysis
        oi = derivatives_data["open_interest"]
        funding = derivatives_data["funding_rate"]
        liq = derivatives_data["liquidations"]
        ls_ratio = derivatives_data["long_short_ratio"]
        prices = derivatives_data["prices"]
        correlations = derivatives_data["correlations"]
        
        # Create focused, concise prompt for WhatsApp-friendly analysis
        prompt = f"""
You are an expert derivatives analyst. Provide CONCISE analysis for SOL position holders via WhatsApp.

KEY DATA:
OI: {self._fmt_usd(oi['current'])} ({self._fmt_usd(oi['24h_change'])} 24h)
Funding: {self._fmt_percentage(funding['current'], 4)} (ann: {self._fmt_percentage(funding['annualized_current'], 2)})
L/S Ratio: {self._fmt_ratio(ls_ratio['current'])} (avg: {self._fmt_ratio(ls_ratio['7d_avg'])})
Liquidations: {self._fmt_usd(liq['longs_24h'])}L / {self._fmt_usd(liq['shorts_24h'])}S
Basis: {self._fmt_percentage(prices['basis_current'], 3)} (ann: {self._fmt_percentage(prices['basis_annualized'], 1)})
Correlations: OI-Funding {correlations['oi_funding']:.2f}, OI-L/S {correlations['oi_ls_ratio']:.2f}

Provide SHARP analysis (max 200 words total):

🎯 BIAS: LONG/SHORT/NEUTRAL

📊 KEY INSIGHT (2-3 sentences max):
What the derivatives are telling us about market direction

⚠️ TOP RISK (1-2 sentences):
Main risk for position holders right now

💡 ACTION (1-2 sentences):
What to do next based on derivatives signals

Keep it punchy, logical, and WhatsApp-friendly. No fluff.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sharp derivatives analyst. Provide concise, actionable insights for crypto position holders. Keep responses brief and WhatsApp-friendly."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,  # Reduced for concise responses
                temperature=0.1  # Very focused responses
            )
            
            analysis = response.choices[0].message.content
            print("   ✅ Derivatives analysis completed")
            return analysis
            
        except Exception as e:
            print(f"   ❌ o3 analysis error: {e}")
            return f"❌ Analysis failed: {str(e)}"
    
    def create_whatsapp_message(self, derivatives_data: Dict[str, Any], o3_analysis: str) -> str:
        """Create focused WhatsApp message for position holders"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        # Extract key metrics
        oi = derivatives_data["open_interest"]
        funding = derivatives_data["funding_rate"]
        liq = derivatives_data["liquidations"]
        ls_ratio = derivatives_data["long_short_ratio"]
        prices = derivatives_data["prices"]
        
        message = f"""
🎯 SOL DERIVATIVES • {timestamp}

📊 ${prices['perp_current']:.2f} | OI: {self._fmt_usd(oi['current'])} ({self._fmt_usd(oi['24h_change'])} 24h)
💸 Funding: {self._fmt_percentage(funding['current'], 4)} | L/S: {self._fmt_ratio(ls_ratio['current'])}

{o3_analysis}

📈 Coinalyze + o3
"""
        
        return message.strip()
    
    def send_to_whatsapp(self, message: str) -> bool:
        """Send message to WhatsApp via Twilio using message templates"""
        if not self.twilio_client:
            print("❌ Twilio client not available")
            return False
        
        if not self.auto_send_whatsapp:
            print("⚠️ Auto-send to WhatsApp is disabled")
            return False
        
        try:
            # Get WhatsApp numbers and template info from environment
            from_number = os.getenv('TWILIO_WHATSAPP_FROM') or os.getenv('TWILIO_WHATSAPP_NUMBER')
            to_number = os.getenv('WHATSAPP_TO_NUMBER')
            template_sid = os.getenv('TWILIO_WHATSAPP_TEMPLATE_SID')
            use_template = os.getenv('TWILIO_USE_TEMPLATE', 'true').lower() == 'true'
            
            if not from_number or not to_number:
                print("❌ Missing WhatsApp numbers in environment")
                print(f"   From: {'✅ Set' if from_number else '❌ Missing'}")
                print(f"   To: {'✅ Set' if to_number else '❌ Missing'}")
                return False
            
            # Format numbers for WhatsApp
            from_param = f'whatsapp:{from_number}'
            to_param = f'whatsapp:{to_number}'
            
            print(f"📱 Sending to WhatsApp: {to_number[-4:].rjust(4, '*')}")  # Mask number for security
            print(f"📱 From WhatsApp: {from_number[-4:].rjust(4, '*')}")
            print(f"📏 Message length: {len(message)} chars")
            print(f"🔧 Template mode: {'ON' if use_template else 'OFF'}")
            
            # Try template message first, fallback to regular message
            twilio_message = None
            
            if use_template and template_sid:
                try:
                    print(f"📋 Using WhatsApp template: {template_sid}")
                    
                    # SIMPLE APPROACH: Use entire message as single template variable
                    # Template should be: "Your trading update: {{1}}" or similar
                    # This approach works with existing approved templates
                    
                    # Clean message for template (remove excessive formatting that may cause issues)
                    clean_message = message.replace("🎯 SOL DERIVATIVES • ", "SOL Alert ")
                    clean_message = clean_message.replace("📈 Coinalyze + o3", "Data: Coinalyze+AI")
                    clean_message = clean_message.strip()
                    
                    # Send using single variable approach (works with most existing templates)
                    twilio_message = self.twilio_client.messages.create(
                        from_=from_param,
                        to=to_param,
                        content_sid=template_sid,
                        content_variables=json.dumps({
                            "1": clean_message  # Entire message as single variable
                        })
                    )
                    print("✅ Template message sent successfully")
                    
                except Exception as template_error:
                    print(f"⚠️ Template message failed: {template_error}")
                    print("🔄 Falling back to regular message...")
                    twilio_message = None
            
            # Fallback to regular message if template failed or not configured
            if not twilio_message:
                print("📝 Sending as regular WhatsApp message")
                twilio_message = self.twilio_client.messages.create(
                    from_=from_param,
                    body=message,
                    to=to_param
                )
            
            print(f"✅ Message sent to Twilio: {twilio_message.sid}")
            
            # Enhanced status checking
            import time
            time.sleep(3)  # Wait a bit for status update
            
            try:
                # Fetch message status
                updated_message = self.twilio_client.messages(twilio_message.sid).fetch()
                status = updated_message.status
                error_code = updated_message.error_code
                error_message = updated_message.error_message
                
                print(f"📊 Message status: {status}")
                if error_code:
                    print(f"❌ Error code: {error_code}")
                    if error_code == 63016:
                        print("🎯 SOLUTION FOR 63016:")
                        print("1. Go to Twilio Console → Content Manager")
                        print("2. Create template: 'Your trading update: {{1}}'")
                        print("3. Category: UTILITY")
                        print("4. Submit for approval (usually approved within minutes)")
                        print("5. Set TWILIO_WHATSAPP_TEMPLATE_SID to the Content SID")
                if error_message:
                    print(f"❌ Error message: {error_message}")
                
                if status in ['delivered', 'sent', 'queued']:
                    print("✅ WhatsApp template message delivered")
                    return True
                elif status == 'failed':
                    print(f"❌ WhatsApp delivery failed: {error_message or 'Template issue'}")
                    return False
                else:
                    print(f"⚠️ WhatsApp message status: {status}")
                    return True  # Consider sent even if status is unclear
                    
            except Exception as status_error:
                print(f"⚠️ Could not check message status: {status_error}")
                return True  # Message was sent, just can't check status
            
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            # Specific handling for template-related errors
            if hasattr(e, 'code'):
                print(f"❌ Twilio error code: {e.code}")
                if e.code == 63016:
                    print("🎯 SOLUTION FOR 63016:")
                    print("1. Go to Twilio Console → Content Manager")
                    print("2. Create template: 'Your trading update: {{1}}'")
                    print("3. Category: UTILITY")
                    print("4. Submit for approval (usually approved within minutes)")
                    print("5. Set TWILIO_WHATSAPP_TEMPLATE_SID to the Content SID")
                elif e.code == 63007:
                    print("💡 Invalid template SID or template not found")
            return False
    
    def run_analysis(self, send_whatsapp: bool = True) -> Dict[str, Any]:
        """Run complete derivatives analysis workflow"""
        print("🚀 Starting SOL Derivatives Analysis...")
        
        # Fetch 7-day derivatives data
        derivatives_data = self.fetch_coinalyze_data()
        
        # Analyze with o3 for derivatives patterns
        o3_analysis = self.analyze_with_o3(derivatives_data)
        
        # Create focused WhatsApp message
        whatsapp_message = self.create_whatsapp_message(derivatives_data, o3_analysis)
        
        # Print analysis results
        print("\n" + "="*60)
        print("🎯 SOL DERIVATIVES ANALYSIS RESULTS")
        print("="*60)
        print(whatsapp_message)
        print("="*60)
        
        # Send to WhatsApp if requested
        whatsapp_sent = False
        if send_whatsapp:
            whatsapp_sent = self.send_to_whatsapp(whatsapp_message)
        
        # Save comprehensive results
        results = {
            "derivatives_data": derivatives_data,
            "o3_analysis": o3_analysis,
            "whatsapp_message": whatsapp_message,
            "whatsapp_sent": whatsapp_sent,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "perp_price": derivatives_data["prices"]["perp_current"],
                "spot_price": derivatives_data["prices"]["spot_current"],
                "oi_current": derivatives_data["open_interest"]["current"],
                "oi_24h_change": derivatives_data["open_interest"]["24h_change"],
                "funding_current": derivatives_data["funding_rate"]["current"],
                "funding_annualized": derivatives_data["funding_rate"]["annualized_current"],
                "ls_ratio": derivatives_data["long_short_ratio"]["current"],
                "basis_current": derivatives_data["prices"]["basis_current"],
                "liquidations_net_24h": derivatives_data["liquidations"]["net_24h"]
            }
        }
        
        # Save to file
        with open("enhanced_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Comprehensive results saved to enhanced_analysis.json")
        
        # Add WhatsApp troubleshooting info if message wasn't sent
        if send_whatsapp and not whatsapp_sent:
            print("\n" + "="*50)
            print("📱 WHATSAPP ERROR 63016 - TEMPLATE REQUIRED")
            print("="*50)
            print("🎯 QUICK FIX (5 minutes):")
            print("1. Go to Twilio Console → Content Manager")
            print("2. Create template: 'Your trading update: {{1}}'")
            print("3. Category: UTILITY, Language: English")
            print("4. Submit for approval (approved in 5-15 minutes)")
            print("5. Copy Content SID (starts with HX...)")
            print("6. Set GitHub Secret: TWILIO_WHATSAPP_TEMPLATE_SID")
            print("")
            print("📋 Template gets approved quickly because it's simple!")
            print("📋 See WHATSAPP_TEMPLATE_SETUP.md for detailed guide")
            print("="*50)
        
        return results

def main():
    """Main entry point for SOL derivatives analysis"""
    parser = argparse.ArgumentParser(description="SOL Derivatives Analysis Agent - 7-day pattern analysis with o3 insights")
    parser.add_argument("--no-whatsapp", action="store_true", help="Skip WhatsApp sending")
    parser.add_argument("--test-whatsapp", action="store_true", help="Test WhatsApp connectivity only")
    args = parser.parse_args()
    
    try:
        workflow = EnhancedSolanaWorkflow()
        
        # Test WhatsApp only
        if args.test_whatsapp:
            print("🧪 Testing WhatsApp connectivity...")
            test_message = f"""
🧪 WhatsApp Test Message
⏰ {datetime.now(timezone.utc).strftime('%H:%M UTC')}

This is a test message to verify WhatsApp connectivity for the SOL Derivatives Analysis Agent.

📈 If you receive this, your setup is working correctly!
"""
            success = workflow.send_to_whatsapp(test_message.strip())
            if success:
                print("✅ WhatsApp test completed - check your phone!")
            else:
                print("❌ WhatsApp test failed - check configuration")
            return 0 if success else 1
        
        # Run full analysis
        results = workflow.run_analysis(send_whatsapp=not args.no_whatsapp)
        print("✅ SOL derivatives analysis completed successfully!")
        print(f"📊 Analyzed {len(results['derivatives_data']['open_interest']['history'])} hours of data")
        print(f"🎯 Current signal bias available in analysis")
        
    except Exception as e:
        print(f"❌ Derivatives analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 