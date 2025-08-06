#!/usr/bin/env python3
"""
Evolution API Setup Script
Automated setup and testing for Evolution API WhatsApp integration
"""

import os
import time
import json
import qrcode
from io import StringIO
from evolution_whatsapp import EvolutionWhatsApp

def print_qr_code_terminal(qr_url: str):
    """Print QR code to terminal for scanning"""
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create QR code in terminal
        f = StringIO()
        qr.print_ascii(out=f, invert=True)
        f.seek(0)
        
        print("\n" + "="*50)
        print("📱 SCAN THIS QR CODE WITH WHATSAPP")
        print("="*50)
        print(f.getvalue())
        print("="*50)
        print("📱 Open WhatsApp > Settings > Linked Devices > Link a Device")
        print("📱 Scan the QR code above")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"⚠️ Could not generate terminal QR code: {e}")
        print(f"🔗 QR Code URL: {qr_url}")

def setup_evolution_api():
    """Complete setup process for Evolution API"""
    print("🚀 Setting up Evolution API for WhatsApp...")
    
    # Initialize client
    client = EvolutionWhatsApp()
    
    # Step 1: Check if Evolution API is running
    print("\n📡 Step 1: Checking Evolution API connection...")
    if not client.check_connection():
        print("❌ Evolution API is not running!")
        print("💡 Please start Evolution API with:")
        print("   docker-compose -f docker-compose.evolution.yml up -d")
        return False
    
    # Step 2: Create session
    print("\n📱 Step 2: Setting up WhatsApp session...")
    session_created = client.create_session()
    if not session_created:
        print("⚠️ Session might already exist, continuing...")
    
    # Step 3: Check current status
    print("\n🔍 Step 3: Checking session status...")
    status = client.check_session_status()
    
    if status == "open":
        print("✅ WhatsApp is already connected!")
    elif status in ["close", "connecting"]:
        print("📱 WhatsApp needs to be connected...")
        
        # Get QR code
        print("\n📱 Step 4: Getting QR code...")
        qr_code = client.get_qr_code()
        
        if qr_code:
            print_qr_code_terminal(qr_code)
            
            # Wait for connection
            print("⏳ Waiting for WhatsApp connection (60 seconds timeout)...")
            connected = client.wait_for_connection(60)
            
            if not connected:
                print("❌ Connection timeout - please try again")
                return False
        else:
            print("❌ Could not get QR code")
            return False
    
    # Step 5: Test connection and get groups
    print("\n📱 Step 5: Testing WhatsApp functionality...")
    
    # Get groups
    groups = client.get_groups()
    
    if not groups:
        print("⚠️ No WhatsApp groups found!")
        print("💡 Please join at least one WhatsApp group to test messaging")
        return True  # Still successful setup, just no groups
    
    # Step 6: Test message sending
    print(f"\n🧪 Step 6: Testing message send to group '{groups[0].get('name', 'Unknown')}'...")
    
    test_message = f"""🧪 *Evolution API Test Message*

✅ WhatsApp connection successful!
🤖 Solana Analysis Bot is ready
⏰ Time: {time.strftime('%H:%M:%S')}

This is a test message to confirm the Evolution API integration is working properly."""

    success = client.send_text_message(groups[0]['id'], test_message)
    
    if success:
        print("✅ Test message sent successfully!")
        print(f"📱 Check your WhatsApp group '{groups[0].get('name', 'Unknown')}'")
    else:
        print("❌ Test message failed")
        return False
    
    # Step 7: Save group information
    print("\n💾 Step 7: Saving group information...")
    
    group_info = {
        "groups": groups,
        "primary_group_jid": groups[0]['id'],
        "primary_group_name": groups[0].get('name', 'Unknown'),
        "setup_time": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('whatsapp_groups.json', 'w') as f:
        json.dump(group_info, f, indent=2)
    
    print("✅ Group information saved to 'whatsapp_groups.json'")
    
    print("\n🎉 Evolution API setup complete!")
    print("="*50)
    print("✅ WhatsApp connected")
    print(f"✅ Found {len(groups)} groups")
    print("✅ Test message sent")
    print("✅ Ready for automation")
    print("="*50)
    
    return True

def test_analysis_sending():
    """Test sending a sample analysis to WhatsApp group"""
    print("\n🧪 Testing analysis sending...")
    
    # Load group info
    try:
        with open('whatsapp_groups.json', 'r') as f:
            group_info = json.load(f)
        
        primary_group_jid = group_info['primary_group_jid']
        primary_group_name = group_info['primary_group_name']
        
        print(f"📱 Sending test analysis to '{primary_group_name}'...")
        
    except FileNotFoundError:
        print("❌ Group information not found - please run setup first")
        return False
    
    # Create sample analysis data
    sample_analysis = {
        "model_used": "o3-mini",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
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
    
    # Save sample analysis
    with open('test_analysis.json', 'w') as f:
        json.dump(sample_analysis, f, indent=2)
    
    # Send analysis
    from evolution_whatsapp import send_analysis_to_whatsapp_group
    
    success = send_analysis_to_whatsapp_group('test_analysis.json', primary_group_jid)
    
    if success:
        print("✅ Test analysis sent successfully!")
        print(f"📱 Check your WhatsApp group '{primary_group_name}'")
    else:
        print("❌ Test analysis sending failed")
    
    # Cleanup
    if os.path.exists('test_analysis.json'):
        os.remove('test_analysis.json')
    
    return success

if __name__ == "__main__":
    print("🚀 Evolution API Setup and Test")
    print("="*50)
    
    # Run setup
    setup_success = setup_evolution_api()
    
    if setup_success:
        # Test analysis sending
        print("\n" + "="*50)
        analysis_success = test_analysis_sending()
        
        if analysis_success:
            print("\n🎉 All tests passed! Evolution API is ready for production.")
        else:
            print("\n⚠️ Setup successful but analysis test failed.")
    else:
        print("\n❌ Setup failed. Please check the steps above.")