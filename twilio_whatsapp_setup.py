#!/usr/bin/env python3
"""
Twilio WhatsApp Integration - EASIEST METHOD
No browser needed, works in GitHub Actions
"""

import os
import json
from datetime import datetime
from twilio.rest import Client
from typing import Optional

class TwilioWhatsApp:
    def __init__(self):
        # Get Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # Your Twilio WhatsApp number
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')  # Recipient's WhatsApp number
        
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            print("⚠️ Twilio credentials not found in environment variables")
            print("Please set: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, WHATSAPP_TO_NUMBER")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            print("✅ Twilio client initialized successfully")
    
    def send_message(self, message: str, to_number: Optional[str] = None) -> bool:
        """Send WhatsApp message via Twilio"""
        try:
            if not self.client:
                print("❌ Twilio client not initialized")
                return False
            
            target_number = to_number or self.to_number
            
            # Format WhatsApp number (add whatsapp: prefix)
            if not target_number.startswith('whatsapp:'):
                target_number = f"whatsapp:{target_number}"
            
            if not self.from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{self.from_number}"
            else:
                from_number = self.from_number
            
            # Send message via Twilio
            message_obj = self.client.messages.create(
                from_=from_number,
                body=message,
                to=target_number
            )
            
            print(f"✅ Message sent successfully! SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            print(f"❌ Twilio send error: {e}")
            return False
    
    def send_to_group(self, message: str, group_name: str) -> bool:
        """Send to WhatsApp group (requires group invite link or individual numbers)"""
        try:
            # For groups, you need to send to individual numbers
            # You can store multiple numbers in environment
            group_numbers = os.getenv('WHATSAPP_GROUP_NUMBERS', '').split(',')
            
            if not group_numbers or group_numbers[0] == '':
                print("⚠️ No group numbers configured. Add WHATSAPP_GROUP_NUMBERS to .env")
                return False
            
            success_count = 0
            for number in group_numbers:
                number = number.strip()
                if number:
                    if self.send_message(message, number):
                        success_count += 1
            
            print(f"✅ Sent to {success_count}/{len(group_numbers)} group members")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Group send error: {e}")
            return False
    
    def format_analysis_for_whatsapp(self, analysis_data: dict) -> str:
        """Format analysis data for WhatsApp (character limit: 4096)"""
        try:
            # Extract the analysis text
            analysis_text = analysis_data.get('analysis', '')
            
            # Add timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
            
            # Format for WhatsApp (emojis work great)
            formatted_message = f"""
🔔 SOLANA ANALYSIS REPORT
⏰ {timestamp}
{'='*40}

{analysis_text}

{'='*40}
📊 Powered by o3 AI Analysis
⚠️ Educational purposes only
            """.strip()
            
            # Check length (WhatsApp limit: 4096 characters)
            if len(formatted_message) > 4000:
                # Truncate if too long
                formatted_message = formatted_message[:3990] + "\n\n[Message truncated...]"
            
            return formatted_message
            
        except Exception as e:
            print(f"❌ Format error: {e}")
            return "Error formatting analysis for WhatsApp"

def send_analysis_via_twilio(analysis_file: str = 'o3_enhanced_analysis.json', to_group: bool = False):
    """Send the latest analysis via Twilio WhatsApp"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Initialize Twilio sender
        sender = TwilioWhatsApp()
        
        # Format message for WhatsApp
        message = sender.format_analysis_for_whatsapp(analysis_data)
        
        # Send message
        if to_group:
            success = sender.send_to_group(message, "Solana Analysis")
        else:
            success = sender.send_message(message)
        
        if success:
            print("🎯 Analysis sent via Twilio WhatsApp successfully!")
        else:
            print("❌ Failed to send analysis via Twilio")
            
        return success
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending via Twilio: {e}")
        return False

if __name__ == "__main__":
    # Test Twilio WhatsApp integration
    send_analysis_via_twilio()
