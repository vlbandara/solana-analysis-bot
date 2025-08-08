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
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        print(f"🔍 DEBUG: Account SID: {'✅ Set' if self.account_sid else '❌ Missing'}")
        print(f"🔍 DEBUG: Auth Token: {'✅ Set' if self.auth_token else '❌ Missing'}")
        print(f"🔍 DEBUG: From Number: {'✅ Set' if self.from_number else '❌ Missing'}")
        print(f"🔍 DEBUG: To Number: {'✅ Set' if self.to_number else '❌ Missing'}")
        
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            print("⚠️ Missing Twilio credentials in .env file")
            self.client = None
        elif TWILIO_AVAILABLE:
            print("🔍 DEBUG: Creating Twilio client...")
            self.client = Client(self.account_sid, self.auth_token)
            print("✅ DEBUG: Twilio client created successfully")
        else:
            print("❌ DEBUG: Twilio library not available")
            self.client = None

    

    def send_message(self, message: str, template_vars: dict | None = None) -> bool:
        """Send message to WhatsApp"""
        print("🔍 DEBUG: Attempting to send WhatsApp message...")
        if not self.client:
            print("❌ Twilio client not available")
            return False
        
        try:
            print(f"🔍 DEBUG: Sending to: whatsapp:{self.to_number}")
            print(f"🔍 DEBUG: From: whatsapp:{self.from_number}")
            from_param = f'whatsapp:{self.from_number}'
            to_param   = f'whatsapp:{self.to_number}'
            template_sid = os.getenv('TWILIO_TEMPLATE_SID')
            
            if template_sid and template_vars:
                print(f"🔍 DEBUG: Using template SID {template_sid}")
                print(f"🔍 DEBUG: Template variables: {template_vars}")
                message = self.client.messages.create(
                    from_=from_param,
                    to=to_param,
                    content_sid=template_sid,
                    content_variables=json.dumps(template_vars)
                )
            else:
                print("🔍 DEBUG: Using direct message (no template)")
                message = self.client.messages.create(
                    from_=from_param,
                    body=message,
                    to=to_param
                )
            print(f"✅ Twilio accepted message: {message.sid}. Checking delivery status …")
            try:
                # poll up to ~20 s for delivered/failed
                import time
                for _ in range(10):
                    status = self.client.messages(message.sid).fetch().status
                    print(f"   ↪ current status: {status}")
                    if status in {"delivered","failed","undelivered"}:
                        break
                    time.sleep(2)
                if status == "delivered":
                    print("✅ WhatsApp reports DELIVERED")
                    return True
                else:
                    print(f"⚠️ Message not delivered (final status: {status}). Check opt-in / template / sandbox join.")
                    return False
            except Exception as ex:
                print(f"⚠️ Could not verify delivery status: {ex}")
                return True
        except TwilioException as e:
            print(f"❌ Twilio error: {e}")
            return False
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            return False

    def send_analysis_with_template(self, analysis: str) -> bool:
        """Send analysis using Twilio template with parsed variables"""
        try:
            # Parse the analysis to extract template variables
            template_vars = self._parse_analysis_for_template(analysis)
            
            if template_vars:
                print("🔍 DEBUG: Using template with variables")
                return self.send_message("", template_vars)
            else:
                print("🔍 DEBUG: Falling back to direct message")
                return self.send_message(analysis)
                
        except Exception as e:
            print(f"❌ Error sending analysis with template: {e}")
            return False

    def _parse_analysis_for_template(self, analysis: str) -> dict | None:
        """Parse analysis text to extract template variables"""
        try:
            lines = analysis.split('\n')
            template_vars = {}
            
            # Extract signal
            for line in lines:
                if "🚨 SIGNAL:" in line or "🚨 **SIGNAL**:" in line:
                    signal = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    signal = signal.replace("**", "").replace("*", "")
                    template_vars["1"] = signal
                    break
            
            # Extract setup
            for i, line in enumerate(lines):
                if "📊 SETUP:" in line or "📊 **SETUP**:" in line:
                    setup_lines = []
                    # Get the setup content from the same line
                    setup_content = line.split(":", 1)[1].strip()
                    setup_content = setup_content.replace("**", "").replace("*", "")
                    if setup_content:
                        setup_lines.append(setup_content)
                    
                    # Check for additional setup lines
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line.startswith("📰") or next_line.startswith("🎯"):
                            break
                        if next_line:
                            # Remove markdown formatting
                            next_line = next_line.replace("**", "").replace("*", "")
                            setup_lines.append(next_line)
                    template_vars["2"] = " ".join(setup_lines)
                    break
            
            # Extract news
            for line in lines:
                if "📰 NEWS:" in line or "📰 **NEWS**:" in line:
                    news = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    news = news.replace("**", "").replace("*", "")
                    template_vars["3"] = news
                    break
            
            # Extract entry
            for line in lines:
                if "🎯 ENTRY:" in line or "🎯 **ENTRY**:" in line:
                    entry = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    entry = entry.replace("**", "").replace("*", "")
                    template_vars["4"] = entry
                    break
            
            # Extract stop
            for line in lines:
                if "⛔ STOP:" in line or "⛔ **STOP**:" in line:
                    stop = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    stop = stop.replace("**", "").replace("*", "")
                    template_vars["5"] = stop
                    break
            
            # Extract target
            for line in lines:
                if "🎪 TARGET:" in line or "🎪 **TARGET**:" in line:
                    target = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    target = target.replace("**", "").replace("*", "")
                    template_vars["6"] = target
                    break
            
            # Extract risk
            for line in lines:
                if "⚠️ RISK:" in line or "⚠️ **RISK**:" in line:
                    risk = line.split(":", 1)[1].strip()
                    # Remove markdown formatting
                    risk = risk.replace("**", "").replace("*", "")
                    template_vars["7"] = risk
                    break
            
            # Check if we have all required variables
            required_vars = ["1", "2", "3", "4", "5", "6", "7"]
            if all(var in template_vars for var in required_vars):
                print(f"✅ Parsed template variables: {template_vars}")
                return template_vars
            else:
                print(f"⚠️ Missing template variables. Found: {list(template_vars.keys())}")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing analysis for template: {e}")
            return None
    
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