#!/usr/bin/env python3
"""
Test script for Twilio template integration
"""

import os
from dotenv import load_dotenv
from whatsapp_sender import WhatsAppSender

def test_template():
    """Test the template functionality"""
    load_dotenv()
    
    # Test message that matches your analysis format
    test_analysis = """🚨 SIGNAL: LONG (Short-term)
📊 SETUP: SOL recovering from $168-171 demand zone with declining OI (-1.1% 24h) while price rises (+1.1%) - classic short covering pattern. Long/short ratio dropped to 2.69 from 2.79 average, yet $1.7M shorts liquidated vs only $0.7M longs. Price approaching key supply zone at $175 where previous rejections occurred.
📰 NEWS: None (last 60 minutes)
🎯 ENTRY: $170-172 (current level)
⛔ STOP: $167.50 (below demand zone)
🎪 TARGET: $175 (first resistance), $180 (extended)
⚠️ RISK: Heavy resistance at $175 level where price previously rejected. Declining OI suggests weak conviction - could reverse quickly if shorts stop covering."""

    print("🧪 Testing Twilio template integration...")
    print("=" * 50)
    
    # Check environment variables
    template_sid = os.getenv('TWILIO_TEMPLATE_SID')
    print(f"📋 Template SID: {'✅ Set' if template_sid else '❌ Missing'}")
    
    # Test WhatsApp sender
    sender = WhatsAppSender()
    
    # Test template parsing
    print("\n🔍 Testing template variable parsing...")
    template_vars = sender._parse_analysis_for_template(test_analysis)
    
    if template_vars:
        print("✅ Template variables parsed successfully:")
        for key, value in template_vars.items():
            print(f"   {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
    else:
        print("❌ Template variable parsing failed")
    
    # Test sending (optional - uncomment to actually send)
    print("\n📱 Template integration ready!")
    print("💡 To test actual sending, uncomment the send_analysis_with_template line")
    
    # Uncomment the next line to actually send a test message
    # success = sender.send_analysis_with_template(test_analysis)
    # print(f"📤 Send result: {'✅ Success' if success else '❌ Failed'}")

if __name__ == "__main__":
    test_template()
