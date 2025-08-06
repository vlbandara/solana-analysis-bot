#!/usr/bin/env python3
"""
Enhanced WhatsApp Sender Module for Solana Analysis Bot
Supports both Twilio API and Evolution API for WhatsApp messaging
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    from evolution_whatsapp import EvolutionWhatsApp, send_analysis_to_whatsapp_group
    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False
    print("⚠️ Evolution API module not available")

class EnhancedWhatsAppSender:
    """Enhanced WhatsApp sender supporting both Twilio and Evolution API"""
    
    def __init__(self, prefer_evolution: bool = True):
        """Initialize WhatsApp sender with preferred method"""
        self.prefer_evolution = prefer_evolution and EVOLUTION_AVAILABLE
        self.twilio_client = None
        self.evolution_client = None
        self.group_jid = None
        
        print(f"🔍 Initializing Enhanced WhatsApp Sender...")
        print(f"📱 Evolution API available: {'✅' if EVOLUTION_AVAILABLE else '❌'}")
        print(f"📱 Twilio available: {'✅' if TWILIO_AVAILABLE else '❌'}")
        print(f"📱 Preferred method: {'Evolution API' if self.prefer_evolution else 'Twilio'}")
        
        # Initialize Evolution API if preferred and available
        if self.prefer_evolution:
            self._init_evolution()
        
        # Initialize Twilio as fallback
        if TWILIO_AVAILABLE:
            self._init_twilio()
    
    def _init_evolution(self):
        """Initialize Evolution API client"""
        try:
            self.evolution_client = EvolutionWhatsApp()
            
            # Check if Evolution API is running
            if self.evolution_client.check_connection():
                # Check session status
                status = self.evolution_client.check_session_status()
                if status == "open":
                    print("✅ Evolution API connected and ready")
                    
                    # Load group information if available
                    try:
                        with open('whatsapp_groups.json', 'r') as f:
                            group_info = json.load(f)
                        self.group_jid = group_info.get('primary_group_jid')
                        print(f"📱 Primary group loaded: {group_info.get('primary_group_name', 'Unknown')}")
                    except FileNotFoundError:
                        print("⚠️ No group information found - run setup_evolution.py first")
                else:
                    print(f"⚠️ Evolution API session not connected (status: {status})")
                    self.evolution_client = None
            else:
                print("⚠️ Evolution API not available")
                self.evolution_client = None
                
        except Exception as e:
            print(f"⚠️ Evolution API initialization failed: {e}")
            self.evolution_client = None
    
    def _init_twilio(self):
        """Initialize Twilio client"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                print("✅ Twilio client initialized")
            else:
                print("⚠️ Twilio credentials not found")
                
        except Exception as e:
            print(f"⚠️ Twilio initialization failed: {e}")
            self.twilio_client = None
    
    def send_message(self, message: str, template_vars: dict = None) -> bool:
        """Send message using preferred method with fallback"""
        
        # Try Evolution API first if preferred and available
        if self.prefer_evolution and self.evolution_client and self.group_jid:
            print("📱 Sending via Evolution API...")
            success = self.evolution_client.send_text_message(self.group_jid, message)
            if success:
                print("✅ Message sent via Evolution API")
                return True
            else:
                print("⚠️ Evolution API failed, trying Twilio fallback...")
        
        # Fallback to Twilio
        if self.twilio_client:
            print("📱 Sending via Twilio...")
            return self._send_twilio_message(message, template_vars)
        
        print("❌ No available WhatsApp method")
        return False
    
    def _send_twilio_message(self, message: str, template_vars: dict = None) -> bool:
        """Send message via Twilio (original implementation)"""
        try:
            from_number = os.getenv('TWILIO_WHATSAPP_FROM') or os.getenv('TWILIO_WHATSAPP_NUMBER')
            to_number = os.getenv('WHATSAPP_TO_NUMBER') or os.getenv('AUTO_SEND_TO_WHATSAPP')
            
            if not all([from_number, to_number]):
                print("❌ Twilio WhatsApp numbers not configured")
                return False
            
            from_param = f'whatsapp:{from_number}'
            to_param = f'whatsapp:{to_number}'
            
            template_sid = os.getenv('TWILIO_TEMPLATE_SID')
            if template_sid and template_vars:
                message_obj = self.twilio_client.messages.create(
                    from_=from_param,
                    to=to_param,
                    content_sid=template_sid,
                    content_variables=json.dumps(template_vars)
                )
            else:
                message_obj = self.twilio_client.messages.create(
                    from_=from_param,
                    body=message,
                    to=to_param
                )
            
            print(f"✅ Twilio message sent: {message_obj.sid}")
            return True
            
        except Exception as e:
            print(f"❌ Twilio error: {e}")
            return False
    
    def send_analysis_summary(self, analysis_data: Dict[str, Any]) -> bool:
        """Send analysis summary using preferred method"""
        
        # Try Evolution API first if preferred and available
        if self.prefer_evolution and self.evolution_client and self.group_jid:
            print("📱 Sending analysis via Evolution API...")
            success = self.evolution_client.send_analysis_to_group(self.group_jid, analysis_data)
            if success:
                print("✅ Analysis sent via Evolution API")
                return True
            else:
                print("⚠️ Evolution API failed, trying Twilio fallback...")
        
        # Fallback to Twilio with formatted message
        if self.twilio_client:
            print("📱 Sending analysis via Twilio...")
            summary = self._create_whatsapp_summary(analysis_data)
            return self._send_twilio_message(summary)
        
        print("❌ No available WhatsApp method for analysis")
        return False
    
    def _create_whatsapp_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Create WhatsApp-friendly summary (shared with original implementation)"""
        model_used = analysis_data.get('model_used', 'Unknown')
        timestamp = analysis_data.get('timestamp', '')
        analysis = analysis_data.get('analysis', '')
        
        lines = analysis.split('\n')
        summary_lines = []
        
        # Add header
        summary_lines.append("🚀 SOLANA ANALYSIS UPDATE")
        summary_lines.append("=" * 30)
        
        # Extract price and key metrics
        price_info = ""
        for line in lines:
            if "Spot reference:" in line or "Current Price:" in line:
                price_parts = line.split("$")
                if len(price_parts) > 1:
                    price_info = price_parts[-1].split()[0]
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
                parts = line.split("$")
                if len(parts) > 1:
                    support_level = parts[-1].split()[0]
            if "R1" in line and "$" in line:
                parts = line.split("$")
                if len(parts) > 1:
                    resistance_level = parts[-1].split()[0]
        
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
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of both WhatsApp methods"""
        status = {
            "evolution_api": {
                "available": EVOLUTION_AVAILABLE,
                "connected": False,
                "group_configured": bool(self.group_jid)
            },
            "twilio": {
                "available": TWILIO_AVAILABLE,
                "configured": bool(self.twilio_client)
            },
            "preferred_method": "evolution" if self.prefer_evolution else "twilio"
        }
        
        if self.evolution_client:
            try:
                session_status = self.evolution_client.check_session_status()
                status["evolution_api"]["connected"] = (session_status == "open")
                status["evolution_api"]["session_status"] = session_status
            except:
                pass
        
        return status

def send_analysis_to_whatsapp(analysis_file: str, prefer_evolution: bool = True) -> bool:
    """Enhanced function to send analysis with Evolution API support"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Create enhanced sender
        sender = EnhancedWhatsAppSender(prefer_evolution=prefer_evolution)
        
        # Send analysis
        return sender.send_analysis_summary(analysis_data)
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending to WhatsApp: {e}")
        return False

def send_alert_to_whatsapp(message: str, prefer_evolution: bool = True) -> bool:
    """Enhanced function to send alerts with Evolution API support"""
    sender = EnhancedWhatsAppSender(prefer_evolution=prefer_evolution)
    return sender.send_message(message)

if __name__ == "__main__":
    # Test enhanced WhatsApp sender
    print("🧪 Testing Enhanced WhatsApp Sender")
    print("=" * 40)
    
    sender = EnhancedWhatsAppSender()
    
    # Show status
    status = sender.get_status()
    print("📊 WhatsApp Status:")
    print(json.dumps(status, indent=2))
    
    # Test message
    test_message = f"""🧪 *Enhanced WhatsApp Test*

✅ Multi-method support active
🔄 Evolution API + Twilio fallback
⏰ Time: {datetime.now().strftime('%H:%M:%S')}

This message was sent using the enhanced WhatsApp sender with automatic fallback capability."""

    print(f"\n📱 Sending test message...")
    success = sender.send_message(test_message)
    
    if success:
        print("✅ Enhanced WhatsApp test successful!")
    else:
        print("❌ Enhanced WhatsApp test failed!")