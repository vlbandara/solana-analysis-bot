#!/usr/bin/env python3
"""
Simple WhatsApp Test - Send a test message to verify setup
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_whatsapp():
    try:
        from twilio.rest import Client
        
        # Get credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
        from_number = os.getenv('TWILIO_WHATSAPP_FROM')
        to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        print(f"📱 Testing WhatsApp delivery...")
        print(f"   From: {from_number}")
        print(f"   To: {to_number}")
        
        if not all([account_sid, auth_token, from_number, to_number]):
            print("❌ Missing environment variables!")
            print("   Set: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, WHATSAPP_TO_NUMBER")
            return
        
        # Create client and send test message
        client = Client(account_sid, auth_token)
        
        test_message = """🧪 WhatsApp Test Message

This is a test from your SOL Derivatives Analysis Agent.

If you received this, your WhatsApp setup is working! 🎉

Next hourly analysis will be sent at the top of the hour."""

        message = client.messages.create(
            from_=f'whatsapp:{from_number}',
            body=test_message,
            to=f'whatsapp:{to_number}'
        )
        
        print(f"✅ Test message sent!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print(f"\n📱 Check your WhatsApp now!")
        print(f"🔍 Track delivery: https://console.twilio.com/us1/develop/sms/logs/{message.sid}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n💡 Common fixes:")
        print(f"   1. Complete WhatsApp sandbox opt-in first")
        print(f"   2. Check phone number format (+1234567890)")
        print(f"   3. Verify Twilio credentials")

if __name__ == "__main__":
    test_whatsapp()