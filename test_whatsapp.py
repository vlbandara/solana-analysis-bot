#!/usr/bin/env python3
"""
Test script for WhatsApp integration
"""

import os
from whatsapp_sender import WhatsAppSender, send_alert_to_whatsapp

def test_whatsapp_integration():
    """Test WhatsApp integration with detailed debugging"""
    print("🧪 Testing WhatsApp Integration")
    print("=" * 40)
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    env_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_WHATSAPP_FROM',
        'WHATSAPP_TO_NUMBER'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n🔍 Testing WhatsApp sender initialization...")
    sender = WhatsAppSender()
    
    print("\n🔍 Testing simple message send...")
    test_message = "🧪 Test message from Solana Analysis Bot\nTime: " + os.popen('date').read().strip()
    
    success = send_alert_to_whatsapp(test_message)
    
    if success:
        print("✅ WhatsApp test successful!")
        return True
    else:
        print("❌ WhatsApp test failed!")
        return False

if __name__ == "__main__":
    test_whatsapp_integration() 