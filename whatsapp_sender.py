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
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM')
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            print("⚠️ Missing Twilio credentials in .env file")
            self.client = None
        elif TWILIO_AVAILABLE:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    def send_message(self, message: str) -> bool:
        """Send message to WhatsApp"""
        if not self.client:
            print("❌ Twilio client not available")
            return False
        
        try:
            message = self.client.messages.create(
                from_=f'whatsapp:{self.from_number}',
                body=message,
                to=f'whatsapp:{self.to_number}'
            )
            print(f"✅ WhatsApp message sent: {message.sid}")
            return True
        except TwilioException as e:
            print(f"❌ Twilio error: {e}")
            return False
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            return False
    
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