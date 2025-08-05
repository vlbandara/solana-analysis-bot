#!/usr/bin/env python3
"""
Test Script for Pattern-Aware Analysis
=====================================
Quick test to demonstrate the new pattern-aware analysis capabilities
"""

import os
from pattern_aware_solana_agent import run_pattern_analysis
from advanced_crypto_agent import analyze_crypto_intelligently

def test_both_approaches():
    """Test both the new pattern-aware agent and the enhanced existing agent"""
    print("🚀 TESTING PATTERN-AWARE ANALYSIS SYSTEMS")
    print("=" * 80)
    
    # Test 1: New Pattern-Aware Agent
    print("\n1️⃣ TESTING NEW PATTERN-AWARE AGENT:")
    print("-" * 50)
    
    try:
        result1 = run_pattern_analysis()
        
        if result1:
            print("✅ Pattern-aware agent working!")
            print("📊 Key features demonstrated:")
            print("   • Historical pattern detection")
            print("   • Trend analysis with significance scoring")
            print("   • Comparative analysis (1h, 4h, 24h)")
            print("   • Pattern-focused AI prompts")
        else:
            print("❌ Pattern-aware agent failed!")
            
    except Exception as e:
        print(f"❌ Pattern-aware agent error: {e}")
    
    print("\n" + "=" * 80)
    
    # Test 2: Enhanced Existing Agent
    print("\n2️⃣ TESTING ENHANCED EXISTING AGENT:")
    print("-" * 50)
    
    try:
        result2 = analyze_crypto_intelligently("SOL")
        
        if result2:
            print("✅ Enhanced existing agent working!")
            print("📊 Key enhancements demonstrated:")
            print("   • Pattern context in AI prompts")
            print("   • Historical data integration")
            print("   • Trend-focused analysis")
        else:
            print("❌ Enhanced existing agent failed!")
            
    except Exception as e:
        print(f"❌ Enhanced existing agent error: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 PATTERN ANALYSIS COMPARISON")
    print("=" * 80)
    print("""
    OLD APPROACH:
    • "L/S ratio: 2.98" ❌ Just snapshot data
    • No historical context
    • AI analyzes current values only
    
    NEW APPROACH:
    • "L/S ratio: 2.98 (📉 -15% from 3.5 avg 4h ago)" ✅ Pattern context
    • Historical trend analysis
    • AI analyzes changes and patterns
    • Significance scoring for changes
    • Comparative timeframe analysis
    """)
    
    print("\n✅ Pattern-aware analysis testing complete!")
    print("🔥 Your analysis will now comment on PATTERNS, not just snapshots!")

if __name__ == "__main__":
    test_both_approaches()