#!/usr/bin/env python3
"""
Clean O3 Workflow
=================
Single, clean workflow using the new single_o3_solana_agent.
No messy fallbacks, no multiple calls - just pure o3 intelligence.
"""

import os
import sys
from datetime import datetime
from single_o3_solana_agent import run_single_o3_analysis

def send_to_whatsapp(analysis_data):
    """Send analysis to WhatsApp if enabled"""
    if not analysis_data:
        return False
    
    try:
        from whatsapp_sender import WhatsAppSender
        
        whatsapp_content = analysis_data.get('whatsapp_format')
        if not whatsapp_content:
            print("⚠️ No WhatsApp format available")
            return False
        
        sender = WhatsAppSender()
        result = sender.send_message(whatsapp_content)
        
        if result:
            print("✅ Analysis sent to WhatsApp!")
            return True
        else:
            print("❌ WhatsApp send failed!")
            return False
            
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        return False

def main():
    """Clean, single o3 workflow"""
    start_time = datetime.now()
    
    print("🚀 CLEAN O3 SOL DERIVATIVES WORKFLOW")
    print("=" * 80)
    print("🧠 Single o3 call with ALL data fed at once")
    print("🎯 No messy fallbacks - pure o3 intelligence")
    print("=" * 80)
    
    print(f"⏰ Starting at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Single comprehensive analysis
    result = run_single_o3_analysis()
    
    if result:
        print(f"\n✅ ANALYSIS COMPLETE")
        print("=" * 80)
        print("🧠 Single o3 call with comprehensive data synthesis")
        print("📊 All derivatives metrics analyzed in one intelligent pass")
        print(f"🎯 Data quality: {result.get('data_quality', 'unknown')}")
        
        # WhatsApp integration
        auto_send = os.getenv('AUTO_SEND_TO_WHATSAPP', 'false').lower() == 'true'
        if auto_send:
            print("\n📱 Auto-sending to WhatsApp...")
            send_to_whatsapp(result)
        else:
            print("\n📱 Set AUTO_SEND_TO_WHATSAPP=true to enable auto-send")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"⏱️ Total analysis time: {duration:.1f}s")
        
        return result
    else:
        print("\n❌ ANALYSIS FAILED")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean O3 SOL Derivatives Workflow")
    parser.add_argument("--whatsapp", action="store_true", help="Force send to WhatsApp")
    
    args = parser.parse_args()
    
    # Set environment for this run
    if args.whatsapp:
        os.environ['AUTO_SEND_TO_WHATSAPP'] = 'true'
    
    result = main()
    
    if result and args.whatsapp and not os.getenv('AUTO_SEND_TO_WHATSAPP'):
        # Manual WhatsApp send if requested
        send_to_whatsapp(result)
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)