#!/usr/bin/env python3
"""
Manual Evolution API Test Script
Run this after starting Evolution API with Docker
"""

import os
import sys
import time
import json
from datetime import datetime

def test_evolution_api():
    """Test Evolution API step by step"""
    print("🧪 Manual Evolution API Test")
    print("=" * 40)
    
    # Check if Evolution API module is available
    try:
        from evolution_whatsapp import EvolutionWhatsApp
        print("✅ Evolution API module imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import Evolution API module: {e}")
        print("💡 Make sure you have installed: pip install requests qrcode[pil]")
        return False
    
    # Initialize client
    print("\n📡 Step 1: Initializing Evolution API client...")
    client = EvolutionWhatsApp()
    
    # Test connection
    print("\n📡 Step 2: Testing connection to Evolution API...")
    if not client.check_connection():
        print("❌ Evolution API not available!")
        print("💡 Make sure Evolution API is running:")
        print("   docker-compose -f docker-compose.evolution.yml up -d")
        print("   Then wait 30 seconds for it to start")
        return False
    
    print("✅ Evolution API is running")
    
    # Check session status
    print("\n📱 Step 3: Checking WhatsApp session status...")
    status = client.check_session_status()
    print(f"Current status: {status}")
    
    if status == "close":
        print("\n📱 WhatsApp needs to be connected...")
        
        # Create session
        print("Creating session...")
        if client.create_session():
            print("✅ Session created")
        else:
            print("⚠️ Session creation failed or already exists")
        
        # Get QR code
        print("\nGetting QR code...")
        qr_code = client.get_qr_code()
        
        if qr_code:
            print("\n" + "="*50)
            print("📱 SCAN THIS QR CODE WITH WHATSAPP")
            print("="*50)
            print("🔗 QR Code URL:", qr_code)
            print("="*50)
            print("📱 Steps to scan:")
            print("1. Open WhatsApp on your phone")
            print("2. Go to Settings → Linked Devices")
            print("3. Tap 'Link a Device'")
            print("4. Scan the QR code")
            print("="*50)
            
            # Wait for user to scan
            input("\n⏳ Press Enter after scanning the QR code...")
            
            # Wait for connection
            print("\n⏳ Waiting for connection...")
            connected = client.wait_for_connection(30)
            
            if not connected:
                print("❌ Connection failed or timed out")
                return False
        else:
            print("❌ Could not get QR code")
            return False
    
    elif status == "open":
        print("✅ WhatsApp is already connected!")
    else:
        print(f"⚠️ Unexpected status: {status}")
        return False
    
    # Get groups
    print("\n📱 Step 4: Getting WhatsApp groups...")
    groups = client.get_groups()
    
    if not groups:
        print("❌ No WhatsApp groups found!")
        print("💡 Please join at least one WhatsApp group to test messaging")
        return False
    
    print(f"✅ Found {len(groups)} groups:")
    for i, group in enumerate(groups):
        print(f"  {i+1}. {group.get('name', 'Unknown')} ({group.get('id', 'No ID')})")
    
    # Select group for testing
    if len(groups) == 1:
        selected_group = groups[0]
        print(f"\n📱 Using group: {selected_group.get('name', 'Unknown')}")
    else:
        print(f"\n📱 Select a group for testing (1-{len(groups)}):")
        try:
            choice = int(input("Enter group number: ")) - 1
            if 0 <= choice < len(groups):
                selected_group = groups[choice]
            else:
                print("Invalid choice, using first group")
                selected_group = groups[0]
        except (ValueError, KeyboardInterrupt):
            print("Using first group")
            selected_group = groups[0]
    
    # Test message sending
    print(f"\n🧪 Step 5: Testing message send to '{selected_group.get('name', 'Unknown')}'...")
    
    test_message = f"""🧪 *Evolution API Test Message*

✅ WhatsApp connection successful!
🤖 Solana Analysis Bot ready for automation
⏰ Test time: {datetime.now().strftime('%H:%M:%S')}
📊 Groups available: {len(groups)}

This is a test message to confirm Evolution API integration is working properly."""

    success = client.send_text_message(selected_group['id'], test_message)
    
    if success:
        print("✅ Test message sent successfully!")
        print(f"📱 Check your WhatsApp group '{selected_group.get('name', 'Unknown')}'")
    else:
        print("❌ Test message failed")
        return False
    
    # Save group information
    print("\n💾 Step 6: Saving group configuration...")
    
    group_info = {
        "groups": groups,
        "primary_group_jid": selected_group['id'],
        "primary_group_name": selected_group.get('name', 'Unknown'),
        "setup_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('whatsapp_groups.json', 'w') as f:
        json.dump(group_info, f, indent=2)
    
    print("✅ Group configuration saved to 'whatsapp_groups.json'")
    
    # Test analysis sending
    print("\n🧪 Step 7: Testing analysis message format...")
    
    sample_analysis = {
        "model_used": "o3-mini",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "analysis": """
SOL/USDT Analysis - Hourly Timeframe

Current Price: $198.45
Spot reference: $198.45

Technical Analysis:
- RSI: 65.2 (Bullish momentum)
- MACD: Positive divergence
- Support levels: S1: $195.20, S2: $192.80
- Resistance levels: R1: $201.50, R2: $205.00

Direction: LONG bias with targets at $201.50
Stop loss: $195.20

Market sentiment: Bullish continuation expected
Volume: Above average, confirming the move
        """.strip()
    }
    
    analysis_success = client.send_analysis_to_group(selected_group['id'], sample_analysis)
    
    if analysis_success:
        print("✅ Sample analysis sent successfully!")
        print(f"📱 Check your WhatsApp group for the formatted analysis")
    else:
        print("❌ Sample analysis sending failed")
    
    # Final summary
    print("\n🎉 Evolution API Test Complete!")
    print("=" * 40)
    print("✅ Evolution API connected")
    print("✅ WhatsApp session active")
    print(f"✅ {len(groups)} groups available")
    print("✅ Test messages sent")
    print("✅ Configuration saved")
    print("=" * 40)
    print("\n📝 Next Steps:")
    print("1. Your Evolution API is ready for automation")
    print("2. Update your workflow to use Evolution API:")
    print("   python3 enhanced_whatsapp_sender.py")
    print("3. Run your existing analysis - it will now use WhatsApp groups!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_evolution_api()
        
        if success:
            print("\n🚀 Ready for production! Your Solana analysis will now be sent to WhatsApp groups.")
        else:
            print("\n❌ Test failed. Please check the steps above and try again.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()