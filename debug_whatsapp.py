#!/usr/bin/env python3
"""
Debug script for WhatsApp template and delivery issues
"""

import os
from dotenv import load_dotenv
from whatsapp_sender import WhatsAppSender

def main():
    """Debug WhatsApp setup"""
    load_dotenv()
    
    print("🔍 WHATSAPP DEBUG SCRIPT")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables Check:")
    print(f"TWILIO_ACCOUNT_SID: {'✅ Set' if os.getenv('TWILIO_ACCOUNT_SID') else '❌ Missing'}")
    print(f"TWILIO_AUTH_TOKEN: {'✅ Set' if os.getenv('TWILIO_AUTH_TOKEN') else '❌ Missing'}")
    print(f"TWILIO_WHATSAPP_FROM: {'✅ Set' if os.getenv('TWILIO_WHATSAPP_FROM') else '❌ Missing'}")
    print(f"TWILIO_TEMPLATE_SID: {'✅ Set' if os.getenv('TWILIO_TEMPLATE_SID') else '❌ Missing'}")
    print(f"WHATSAPP_TO_NUMBERS: {'✅ Set' if os.getenv('WHATSAPP_TO_NUMBERS') else '❌ Missing'}")
    
    # Test template setup
    print("\n🧪 Testing Template Setup:")
    try:
        sender = WhatsAppSender()
        sender.test_template_setup()
    except Exception as e:
        print(f"❌ Template test failed: {e}")
    
    # Check phone number format
    print("\n📱 Phone Number Format Check:")
    numbers = os.getenv('WHATSAPP_TO_NUMBERS', '')
    if numbers:
        print(f"Raw numbers: {numbers}")
        import re
        parts = re.split(r"[\s,;]+", numbers)
        for i, part in enumerate(parts):
            if part.strip():
                clean = part.strip().replace('+', '').replace(' ', '').replace('-', '')
                print(f"  {i+1}. Original: '{part.strip()}' -> Clean: '{clean}' -> Valid: {'✅' if clean.isdigit() else '❌'}")

if __name__ == "__main__":
    main()
