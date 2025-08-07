#!/usr/bin/env python3
"""
Test actual sending with Twilio template
"""

import os
from dotenv import load_dotenv
from whatsapp_sender import WhatsAppSender

def test_actual_send():
    """Test actual sending with template"""
    load_dotenv()
    
    # Test message
    test_analysis = """🚨 SIGNAL: LONG (Short-term)
📊 SETUP: SOL recovering from $168-171 demand zone with declining OI (-1.1% 24h) while price rises (+1.1%) - classic short covering pattern.
📰 NEWS: None (last 60 minutes)
🎯 ENTRY: $170-172 (current level)
⛔ STOP: $167.50 (below demand zone)
🎪 TARGET: $175 (first resistance), $180 (extended)
⚠️ RISK: Heavy resistance at $175 level where price previously rejected."""

    print("🧪 Testing actual WhatsApp sending...")
    
    # Check if Twilio is installed
    try:
        import twilio
        print("✅ Twilio library available")
    except ImportError:
        print("❌ Twilio library not available")
        return
    
    # Test WhatsApp sender
    sender = WhatsAppSender()
    
    if not sender.client:
        print("❌ Twilio client not available")
        return
    
    print("✅ Twilio client ready")
    
    # Test actual sending
    print("\n📱 Testing actual send...")
    success = sender.send_analysis_with_template(test_analysis)
    
    if success:
        print("✅ Message sent successfully!")
    else:
        print("❌ Message sending failed")

if __name__ == "__main__":
    test_actual_send()
