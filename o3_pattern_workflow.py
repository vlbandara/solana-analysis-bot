#!/usr/bin/env python3
"""
O3 Pattern-Aware Trading Workflow
=================================
The new standard workflow that leverages o3's superior reasoning for pattern analysis.
This replaces snapshot-based analysis with intelligent trend detection.

Key Features:
- o3 model prioritized for all analysis
- Pattern-aware data processing
- Historical context integration  
- Comprehensive trend analysis
- WhatsApp integration ready
"""

import os
import sys
from datetime import datetime
from pattern_aware_solana_agent import PatternAwareSolanaAgent, run_pattern_analysis
from advanced_crypto_agent import analyze_crypto_intelligently

def run_o3_pattern_workflow():
    """Main o3-powered pattern-aware workflow"""
    print("🚀 O3 PATTERN-AWARE TRADING WORKFLOW")
    print("=" * 80)
    print("🧠 Leveraging o3's superior reasoning for market pattern analysis")
    print("🔍 Focus: TRENDS and CHANGES, not just snapshots")
    print("=" * 80)
    
    # Step 1: Run Pattern-Aware Analysis
    print("\n📊 STEP 1: PATTERN-AWARE ANALYSIS")
    print("-" * 50)
    
    try:
        print("🔍 Fetching comprehensive historical data for pattern detection...")
        result = run_pattern_analysis()
        
        if result:
            print("✅ Pattern analysis complete!")
            print("🎯 Key patterns identified and analyzed by o3")
            
            # Display key insights
            whatsapp_analysis = result.get('whatsapp_format', '')
            if whatsapp_analysis:
                print("\n📱 FORMATTED ANALYSIS:")
                print("-" * 30)
                print(whatsapp_analysis)
                print("-" * 30)
            
            return result
        else:
            print("❌ Pattern analysis failed!")
            return None
            
    except Exception as e:
        print(f"❌ Pattern workflow error: {e}")
        return None

def run_enhanced_backup_analysis():
    """Backup analysis using enhanced existing agent"""
    print("\n🔄 STEP 2: ENHANCED BACKUP ANALYSIS")
    print("-" * 50)
    
    try:
        print("🧠 Running enhanced analysis with o3 pattern context...")
        result = analyze_crypto_intelligently("SOL")
        
        if result:
            print("✅ Backup analysis complete!")
            return result
        else:
            print("❌ Backup analysis failed!")
            return None
            
    except Exception as e:
        print(f"❌ Backup analysis error: {e}")
        return None

def send_to_whatsapp(analysis_data):
    """Send analysis to WhatsApp if enabled"""
    if not analysis_data:
        return False
    
    try:
        from whatsapp_sender import WhatsAppSender
        
        # Use the formatted WhatsApp content
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
    """Main workflow execution"""
    start_time = datetime.now()
    
    print(f"⏰ Starting workflow at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Primary: Pattern-Aware Analysis with o3
    primary_result = run_o3_pattern_workflow()
    
    # Backup: Enhanced Analysis (if needed)
    backup_result = None
    if not primary_result:
        print("\n⚠️ Primary analysis failed, running backup...")
        backup_result = run_enhanced_backup_analysis()
    
    # Select best result
    final_result = primary_result or backup_result
    
    if final_result:
        print(f"\n✅ WORKFLOW COMPLETE")
        print("=" * 80)
        print("🧠 Analysis powered by o3 model with pattern recognition")
        print("📊 Focus on trends, changes, and market dynamics")
        print("🎯 Superior insights compared to snapshot-only analysis")
        
        # WhatsApp integration
        auto_send = os.getenv('AUTO_SEND_TO_WHATSAPP', 'false').lower() == 'true'
        if auto_send:
            print("\n📱 Auto-sending to WhatsApp...")
            send_to_whatsapp(final_result)
        else:
            print("\n📱 Set AUTO_SEND_TO_WHATSAPP=true to enable auto-send")
        
        # Save comprehensive results
        import json
        with open('o3_pattern_workflow_results.json', 'w') as f:
            json.dump({
                'workflow_version': '2.0_pattern_aware',
                'model_used': 'o3',
                'analysis_type': 'pattern_focused',
                'timestamp': datetime.now().isoformat(),
                'results': final_result
            }, f, indent=2)
        
        print("💾 Full results saved to o3_pattern_workflow_results.json")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"⏱️ Total workflow time: {duration:.1f}s")
        
        return final_result
    else:
        print("\n❌ WORKFLOW FAILED")
        print("Both primary and backup analysis failed!")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="O3 Pattern-Aware Trading Workflow")
    parser.add_argument("--whatsapp", action="store_true", help="Force send to WhatsApp")
    parser.add_argument("--symbol", default="SOL", help="Crypto symbol to analyze")
    
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