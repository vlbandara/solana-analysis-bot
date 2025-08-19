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

        # For WhatsApp, we must use a template for business-initiated messages
        if not template_sid:
            print("❌ TWILIO_TEMPLATE_SID is required for WhatsApp business messages")
            print("💡 Please set TWILIO_TEMPLATE_SID in your environment variables")
            print("💡 You can create a template in Twilio Console or use the default one")
            return False

        print(f"🔍 DEBUG: From WhatsApp number: {self.from_number}")
        print(f"🔍 DEBUG: Template SID: {template_sid}")
        print(f"🔍 DEBUG: Recipients: {recipients}")

        any_success = False
        for recipient in recipients:
            try:
                # Validate phone number format
                clean_number = recipient.replace('+', '').replace(' ', '').replace('-', '')
                if not clean_number.isdigit():
                    print(f"⚠️  Invalid phone number format: {recipient}")
                    continue
                
                to_param = f'whatsapp:{clean_number}'
                print(f"🔍 DEBUG: From: {from_param} -> To: {to_param}")
                print(f"🔍 DEBUG: Using template SID {template_sid}")
                
                # Always use template for WhatsApp business messages
                import json as _json
                msg_obj = self.client.messages.create(
                    from_=from_param,
                    to=to_param,
                    content_sid=template_sid,
                    content_variables=_json.dumps(template_vars or {})
                )
                
                print(f"✅ Twilio accepted message: {msg_obj.sid}. Checking delivery status …")
                try:
                    # poll up to ~20 s for delivered/failed
                    import time
                    status = "queued"
                    for _ in range(10):
                        status = self.client.messages(msg_obj.sid).fetch().status
                        print(f"   ↪ current status for {clean_number}: {status}")
                        if status in {"delivered","failed","undelivered"}:
                            break
                        time.sleep(2)
                    
                    if status == "delivered":
                        print(f"✅ WhatsApp reports DELIVERED to {clean_number}")
                        any_success = True
                    elif status == "undelivered":
                        print(f"⚠️  Message UNDELIVERED to {clean_number}")
                        print(f"💡 Possible causes:")
                        print(f"   - Number not registered with WhatsApp")
                        print(f"   - Incorrect phone number format")
                        print(f"   - WhatsApp Business account setup issue")
                        print(f"   - Template variable mismatch")
                    else:
                        print(f"⚠️ Message not delivered to {clean_number} (final status: {status}).")
                except Exception as ex:
                    print(f"⚠️ Could not verify delivery status for {clean_number}: {ex}")
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
            
            # Create WhatsApp-friendly summary and extract template variables
            summary, template_vars = self._create_whatsapp_summary(analysis, model_used, timestamp)
            
            # Send using template variables
            return self.send_message(summary, template_vars)
            
        except Exception as e:
            print(f"❌ Error creating WhatsApp summary: {e}")
            return False
    
    def _create_whatsapp_summary(self, analysis: str, model_used: str, timestamp: str) -> tuple[str, dict]:
        """Create a WhatsApp message using the approved template format and return template variables"""
        
        # Extract key information from the analysis
        lines = analysis.split('\n')
        
        # Initialize template variables
        template_vars = {
            '1': datetime.now().strftime('%H:%M'),  # Current UTC time
            '2': '0.00',  # Current price
            '3': '0.0',   # 24h change
            '4': '0',     # OI in millions
            '5': '0.0',   # OI change
            '6': '0.000', # Current funding rate
            '7': '0.000', # Funding rate change
            '8': '0.00',  # L/S ratio
            '9': 'WAIT',  # Signal
            '10': 'Analysis unavailable',  # Correlation
            '11': 'No position',  # Positioned
            '12': 'Monitor price action'  # Prepare
        }
        
        # Extract price information
        for line in lines:
            if "Price:" in line and "$" in line:
                try:
                    price_match = line.split("$")[1].split()[0]
                    template_vars['2'] = price_match
                except (IndexError, ValueError):
                    pass
                    
            if "24h)" in line and "%" in line:
                try:
                    change_match = line.split("(")[1].split("%")[0]
                    template_vars['3'] = change_match
                except (IndexError, ValueError):
                    pass
                    
            if "OI:" in line and "$" in line:
                try:
                    oi_match = line.split("$")[1].split("M")[0]
                    template_vars['4'] = oi_match
                except (IndexError, ValueError):
                    pass
                    
            if "OI:" in line and "(" in line and "%" in line:
                try:
                    oi_change = line.split("(")[1].split("%")[0]
                    template_vars['5'] = oi_change
                except (IndexError, ValueError):
                    pass
                    
            if "Funding:" in line and "%" in line:
                try:
                    # Extract current funding rate
                    funding_match = line.split(":")[1].split("%")[0].strip()
                    template_vars['6'] = funding_match
                    
                    # Extract funding rate change (6h Δ)
                    if "6h Δ" in line:
                        change_match = line.split("6h Δ")[1].split("%")[0].strip()
                        template_vars['7'] = change_match
                    elif "Δ" in line:
                        # Alternative format: (6h Δ +0.012%)
                        change_match = line.split("Δ")[1].split("%")[0].strip()
                        template_vars['7'] = change_match
                except (IndexError, ValueError):
                    pass
                    
            if "L/S:" in line:
                try:
                    ls_match = line.split("L/S:")[1].split()[0]
                    template_vars['8'] = ls_match
                except (IndexError, ValueError):
                    pass
                    
            if "SIGNAL:" in line:
                try:
                    signal_match = line.split("SIGNAL:")[1].strip()
                    template_vars['9'] = signal_match
                except (IndexError, ValueError):
                    pass
                    
            if "CORRELATION:" in line:
                try:
                    corr_match = line.split("CORRELATION:")[1].strip()
                    template_vars['10'] = corr_match
                except (IndexError, ValueError):
                    pass
                    
            if "SETUP:" in line:
                try:
                    setup_match = line.split("SETUP:")[1].strip()
                    template_vars['10'] = setup_match  # Use SETUP as correlation
                except (IndexError, ValueError):
                    pass
                    
            # Extract auto signal from features if available
            if "Auto Signal:" in line:
                try:
                    auto_signal = line.split("Auto Signal:")[1].strip()
                    if auto_signal in ["LONG", "SHORT", "WAIT"]:
                        template_vars['9'] = auto_signal
                except (IndexError, ValueError):
                    pass
                    
            # Extract confidence for positioning decision
            if "Confidence:" in line:
                try:
                    confidence = line.split("Confidence:")[1].split("/")[0].strip()
                    conf_num = int(confidence)
                    if conf_num >= 70:
                        template_vars['11'] = "High confidence setup"
                        template_vars['12'] = "Prepare entry zones"
                    elif conf_num >= 50:
                        template_vars['11'] = "Medium confidence"
                        template_vars['12'] = "Monitor for confirmation"
                    else:
                        template_vars['11'] = "Low confidence"
                        template_vars['12'] = "Wait for better setup"
                except (IndexError, ValueError):
                    pass
        
        # Create the template message
        template_message = (
            f"🎯 SOL • {template_vars['1']} UTC\n"
            f"📊 ${template_vars['2']} ({template_vars['3']}% 24h) | OI: ${template_vars['4']}M ({template_vars['5']}%)\n"
            f"💸 {template_vars['6']}% → {template_vars['7']}% | L/S: {template_vars['8']}\n\n"
            f"🚨 SIGNAL: {template_vars['9']}\n"
            f"📊 CORRELATION: {template_vars['10']}\n"
            f"⚠️ POSITIONED: {template_vars['11']}\n"
            f"💡 PREPARE: {template_vars['12']}\n\n"
            f"📈 24h evolution • o3"
        )
        
        return template_message, template_vars

    def test_template_setup(self) -> bool:
        """Test the WhatsApp template setup and variables"""
        print("🧪 Testing WhatsApp template setup...")
        
        template_sid = os.getenv('TWILIO_TEMPLATE_SID')
        if not template_sid:
            print("❌ TWILIO_TEMPLATE_SID not set")
            return False
            
        print(f"✅ Template SID: {template_sid}")
        
        # Test with sample template variables
        test_vars = {
            '1': '12:00',
            '2': '100.00',
            '3': '+2.5',
            '4': '150',
            '5': '+1.2',
            '6': '0.045',
            '7': '+0.012',
            '8': '2.34',
            '9': 'LONG',
            '10': 'Test correlation',
            '11': 'Test positioned',
            '12': 'Test prepare'
        }
        
        print("🔍 Testing template variables:")
        for key, value in test_vars.items():
            print(f"   {{{{{key}}}}} = {value}")
        
        # Test message creation (without sending)
        try:
            test_message, extracted_vars = self._create_whatsapp_summary(
                "Price: $100.00 (+2.5% 24h)\nOI: $150M (+1.2%)\nFunding: 0.045% (6h Δ +0.012%)\nL/S: 2.34\nAuto Signal: LONG\nConfidence: 75/100",
                'Test Model',
                '12:00 UTC'
            )
            
            print("\n✅ Template message created successfully:")
            print(test_message)
            
            print("\n✅ Extracted variables:")
            for key, value in extracted_vars.items():
                print(f"   {key}: {value}")
                
            return True
            
        except Exception as e:
            print(f"❌ Template test failed: {e}")
            return False

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

def test_whatsapp_template():
    """Test function for WhatsApp template setup"""
    try:
        sender = WhatsAppSender()
        return sender.test_template_setup()
    except Exception as e:
        print(f"❌ WhatsApp test failed: {e}")
        return False

if __name__ == "__main__":
    # Test WhatsApp sender
    sender = WhatsAppSender()
    test_message = "🧪 Test message from Solana Analysis Bot"
    success = sender.send_message(test_message)
    
    if success:
        print("✅ WhatsApp test successful!")
    else:
        print("❌ WhatsApp test failed!") 