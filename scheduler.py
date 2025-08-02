#!/usr/bin/env python3
"""
Automated Scheduler for Solana Analysis
Runs analysis and sends to WhatsApp at regular intervals
"""

import os
import time
import schedule
from datetime import datetime
from o3_enhanced_solana_agent import run_o3_enhanced_analysis
from whatsapp_sender import send_analysis_to_whatsapp

def run_analysis_and_send():
    """Run analysis and send to WhatsApp"""
    print(f"\n🕐 Scheduled Analysis Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Run analysis
        results = run_o3_enhanced_analysis()
        
        if results:
            print("✅ Analysis completed successfully")
            
            # Send to WhatsApp if enabled
            if os.getenv('AUTO_SEND_TO_WHATSAPP', 'true').lower() == 'true':
                print("📱 Sending to WhatsApp...")
                whatsapp_success = send_analysis_to_whatsapp()
                
                if whatsapp_success:
                    print("✅ WhatsApp delivery successful")
                else:
                    print("⚠️ WhatsApp delivery failed")
            else:
                print("📱 WhatsApp auto-send disabled")
        else:
            print("❌ Analysis failed")
            
    except Exception as e:
        print(f"❌ Scheduled run error: {e}")

def setup_scheduler():
    """Setup the scheduler with different intervals"""
    
    # Get interval from environment (default: 60 minutes)
    interval_minutes = int(os.getenv('ANALYSIS_INTERVAL_MINUTES', 60))
    
    print(f"⏰ Setting up scheduler for every {interval_minutes} minutes")
    
    if interval_minutes == 60:
        # Every hour
        schedule.every().hour.do(run_analysis_and_send)
        print("📅 Scheduled: Every hour")
    elif interval_minutes == 30:
        # Every 30 minutes
        schedule.every(30).minutes.do(run_analysis_and_send)
        print("📅 Scheduled: Every 30 minutes")
    elif interval_minutes == 15:
        # Every 15 minutes
        schedule.every(15).minutes.do(run_analysis_and_send)
        print("📅 Scheduled: Every 15 minutes")
    else:
        # Custom interval
        schedule.every(interval_minutes).minutes.do(run_analysis_and_send)
        print(f"📅 Scheduled: Every {interval_minutes} minutes")
    
    # Run immediately on startup
    print("🚀 Running initial analysis...")
    run_analysis_and_send()
    
    print(f"\n🔄 Scheduler started. Next run in {interval_minutes} minutes...")
    print("Press Ctrl+C to stop")
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        setup_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Scheduler error: {e}") 