#!/usr/bin/env python3
"""
WhatsApp Integration for Solana Analysis
Sends analysis reports to WhatsApp groups automatically
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional

class WhatsAppSender:
    def __init__(self):
        self.api_key = os.getenv('WHATSAPP_API_KEY')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.group_id = os.getenv('WHATSAPP_GROUP_ID')
        
        if not all([self.api_key, self.phone_number_id, self.access_token, self.group_id]):
            print("⚠️ WhatsApp credentials not found in environment variables")
            print("Please set: WHATSAPP_API_KEY, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_GROUP_ID")
    
    def send_message(self, message: str, group_id: Optional[str] = None) -> bool:
        """Send message to WhatsApp group"""
        try:
            target_group = group_id or self.group_id
            
            url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": target_group,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Message sent to WhatsApp group successfully")
                return True
            else:
                print(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
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

def send_analysis_to_whatsapp(analysis_file: str = 'o3_enhanced_analysis.json'):
    """Send the latest analysis to WhatsApp group"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Initialize WhatsApp sender
        sender = WhatsAppSender()
        
        # Format message for WhatsApp
        message = sender.format_analysis_for_whatsapp(analysis_data)
        
        # Send to group
        success = sender.send_message(message)
        
        if success:
            print("🎯 Analysis sent to WhatsApp group successfully!")
        else:
            print("❌ Failed to send analysis to WhatsApp")
            
        return success
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending to WhatsApp: {e}")
        return False

if __name__ == "__main__":
    # Test WhatsApp integration
    send_analysis_to_whatsapp() 