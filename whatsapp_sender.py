#!/usr/bin/env python3
"""
WhatsApp Sender Module for Solana Analysis Bot
Uses Twilio API to send analysis results to WhatsApp groups
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio not installed. Run: uv add twilio")

class WhatsAppSender:
    """WhatsApp sender using Twilio API"""
    

    def __init__(self):
        """Initialize WhatsApp sender with Twilio credentials"""
        print("🔍 DEBUG: Initializing WhatsApp sender...")
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM') or os.getenv('TWILIO_WHATSAPP_NUMBER')
        # Single number is optional now; multiple numbers supported via WHATSAPP_TO_NUMBERS
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        print(f"🔍 DEBUG: Account SID: {'✅ Set' if self.account_sid else '❌ Missing'}")
        print(f"🔍 DEBUG: Auth Token: {'✅ Set' if self.auth_token else '❌ Missing'}")
        print(f"🔍 DEBUG: From Number: {'✅ Set' if self.from_number else '❌ Missing'}")
        print(f"🔍 DEBUG: To Number: {'✅ Set' if self.to_number else '❌ Missing'}")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            print("⚠️ Missing Twilio credentials (account_sid/auth_token/from). Check environment variables.")
            self.client = None
        elif TWILIO_AVAILABLE:
            print("🔍 DEBUG: Creating Twilio client...")
            self.client = Client(self.account_sid, self.auth_token)
            print("✅ DEBUG: Twilio client created successfully")
        else:
            print("❌ DEBUG: Twilio library not available")
            self.client = None

    

    def _parse_recipients(self) -> list[str]:
        """Parse recipients from WHATSAPP_TO_NUMBERS or fallback to WHATSAPP_TO_NUMBER."""
        raw = os.getenv('WHATSAPP_TO_NUMBERS', '')
        recipients: list[str] = []
        if raw:
            # Split by commas, semicolons, whitespace, or newlines
            import re
            parts = re.split(r"[\s,;]+", raw)
            recipients = [p.strip() for p in parts if p.strip()]
        # Fallback to single number
        if not recipients and self.to_number:
            recipients = [self.to_number.strip()]
        return recipients

    def send_message(self, message: str, template_vars: dict | None = None) -> bool:
        """Send message to all configured WhatsApp recipients."""
        print("🔍 DEBUG: Attempting to send WhatsApp message...")
        if not self.client:
            print("❌ Twilio client not available")
            return False

        recipients = self._parse_recipients()
        if not recipients:
            print("❌ No WhatsApp recipients configured. Set WHATSAPP_TO_NUMBERS or WHATSAPP_TO_NUMBER.")
            return False

        from_param = f'whatsapp:{self.from_number}'
        template_sid = os.getenv('TWILIO_TEMPLATE_SID')

        any_success = False
        for recipient in recipients:
            try:
                to_param = f'whatsapp:{recipient}'
                print(f"🔍 DEBUG: From: {from_param} -> To: {to_param}")
                if template_sid:
                    import json as _json
                    print(f"🔍 DEBUG: Using template SID {template_sid}")
                    msg_obj = self.client.messages.create(
                        from_=from_param,
                        to=to_param,
                        content_sid=template_sid,
                        content_variables=_json.dumps(template_vars or {})
                    )
                else:
                    msg_obj = self.client.messages.create(
                        from_=from_param,
                        body=message,
                        to=to_param
                    )
                print(f"✅ Twilio accepted message: {msg_obj.sid}. Checking delivery status …")
                try:
                    # poll up to ~20 s for delivered/failed
                    import time
                    status = "queued"
                    for _ in range(10):
                        status = self.client.messages(msg_obj.sid).fetch().status
                        print(f"   ↪ current status for {recipient}: {status}")
                        if status in {"delivered","failed","undelivered"}:
                            break
                        time.sleep(2)
                    if status == "delivered":
                        print(f"✅ WhatsApp reports DELIVERED to {recipient}")
                        any_success = True
                    else:
                        print(f"⚠️ Message not delivered to {recipient} (final status: {status}).")
                except Exception as ex:
                    print(f"⚠️ Could not verify delivery status for {recipient}: {ex}")
                    any_success = True  # assume success if Twilio accepted
            except TwilioException as e:
                print(f"❌ Twilio error for {recipient}: {e}")
            except Exception as e:
                print(f"❌ WhatsApp send error for {recipient}: {e}")

        return any_success

    
    def send_analysis_summary(self, analysis_data: Dict[str, Any]) -> bool:
        """Send a concise analysis summary to WhatsApp"""
        try:
            # Extract key information
            model_used = analysis_data.get('model_used', 'Unknown')
            timestamp = analysis_data.get('timestamp', '')
            analysis = analysis_data.get('analysis', '')
            
            # Create WhatsApp-friendly summary
            summary = self._create_whatsapp_summary(analysis, model_used, timestamp)
            
            return self.send_message(summary)
            
        except Exception as e:
            print(f"❌ Error creating WhatsApp summary: {e}")
            return False
    
    def _create_whatsapp_summary(self, analysis: str, model_used: str, timestamp: str) -> str:
        """Create a concise WhatsApp-friendly summary"""
        
        # Extract key trading information
        lines = analysis.split('\n')
        summary_lines = []
        
        # Add header
        summary_lines.append("🚀 SOLANA ANALYSIS UPDATE")
        summary_lines.append("=" * 30)
        
        # Extract price and key metrics
        price_info = ""
        for line in lines:
            if "Spot reference:" in line or "Spot reference:" in line:
                price_info = line.split("$")[-1].split()[0]
                break
        
        if price_info:
            summary_lines.append(f"💰 SOL Price: ${price_info}")
        
        # Extract trading recommendation
        recommendation = "NEUTRAL"
        for line in lines:
            if "Direction:" in line or "Directional Bias:" in line:
                if "LONG" in line.upper():
                    recommendation = "🟢 LONG"
                elif "SHORT" in line.upper():
                    recommendation = "🔴 SHORT"
                break
        
        summary_lines.append(f"📊 Recommendation: {recommendation}")
        
        # Extract key levels
        support_level = "N/A"
        resistance_level = "N/A"
        
        for line in lines:
            if "S1" in line and "$" in line:
                support_level = line.split("$")[-1].split()[0]
            if "R1" in line and "$" in line:
                resistance_level = line.split("$")[-1].split()[0]
        
        summary_lines.append(f"📈 Resistance: ${resistance_level}")
        summary_lines.append(f"📉 Support: ${support_level}")
        
        # Add model info
        summary_lines.append(f"🤖 Model: {model_used}")
        summary_lines.append(f"⏰ Time: {datetime.now().strftime('%H:%M')}")
        
        # Add disclaimer
        summary_lines.append("")
        summary_lines.append("⚠️ Educational purposes only")
        summary_lines.append("📊 Full analysis available in repo")
        
        return "\n".join(summary_lines)

def send_analysis_to_whatsapp(analysis_file: str) -> bool:
    """Send analysis results to WhatsApp"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Create WhatsApp sender
        sender = WhatsAppSender()
        
        # Send summary
        return sender.send_analysis_summary(analysis_data)
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending to WhatsApp: {e}")
        return False

def send_alert_to_whatsapp(message: str) -> bool:
    """Send a simple alert message to WhatsApp"""
    sender = WhatsAppSender()
    return sender.send_message(message)

if __name__ == "__main__":
    # Test WhatsApp sender
    sender = WhatsAppSender()
    test_message = "🧪 Test message from Solana Analysis Bot"
    success = sender.send_message(test_message)
    
    if success:
        print("✅ WhatsApp test successful!")
    else:
        print("❌ WhatsApp test failed!") 