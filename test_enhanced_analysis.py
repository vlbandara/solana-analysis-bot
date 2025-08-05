#!/usr/bin/env python3
"""
Test Enhanced Analysis - Mock Data Demo
=======================================
Shows the new comprehensive analysis without requiring API keys
"""

import json
from sol_hourly_analysis import HourlySolAnalysis
import os

# Mock data that simulates comprehensive API response
mock_data = {
    'timestamp': 1754389200,
    # Current price metrics
    'price': 163.55,
    'price_24h_change': -2.3,
    
    # Open Interest metrics  
    'oi_usd': 1498500000,  # $1.498B
    'oi_24h_change': 3.2,
    
    # Funding metrics
    'funding_pct': -0.212,
    'predicted_funding_pct': -0.267,
    
    # Long/Short ratio metrics
    'ls_ratio': 3.22,
    'ls_24h_avg': 3.45,
    'ls_24h_change': -6.7,
    
    # Liquidation metrics
    'long_liq_24h': 8500000,   # $8.5M
    'short_liq_24h': 2100000,  # $2.1M
    'long_liq_6h': 2300000,    # $2.3M
    'short_liq_6h': 450000,    # $0.45M
    
    # Basis
    'basis_pct': -0.045
}

def test_comprehensive_analysis():
    """Test the comprehensive analysis logic"""
    print("🧪 Testing Enhanced SOL Analysis (Mock Data)")
    print("=" * 60)
    
    # Create analyzer (will use fallback since no API keys)
    os.environ.pop('COINALYZE_API_KEY', None)
    os.environ.pop('OPENAI_API_KEY', None)
    
    try:
        analyzer = HourlySolAnalysis()
    except:
        print("⚠️ Creating minimal analyzer for testing...")
        
        class MockAnalyzer:
            def analyze_with_reasoning(self, current, last=None):
                """Test the enhanced fallback analysis"""
                print("🔍 Analyzing mock data...")
                print(f"   💰 Price: ${current['price']:.2f} ({current['price_24h_change']:+.1f}% 24h)")
                print(f"   🏦 OI: ${current['oi_usd']/1e6:.1f}M ({current['oi_24h_change']:+.1f}% 24h)")
                print(f"   💸 Funding: {current['funding_pct']:.3f}% → {current['predicted_funding_pct']:.3f}%")
                print(f"   ⚖️ L/S: {current['ls_ratio']:.2f} (24h avg: {current['ls_24h_avg']:.2f}, {current['ls_24h_change']:+.1f}%)")
                print(f"   🔥 Liq 24h: ${current['long_liq_24h']/1e6:.1f}M L / ${current['short_liq_24h']/1e6:.1f}M S")
                print(f"   📈 Basis: {current['basis_pct']:.3f}%")
                print()
                
                # Enhanced fallback logic
                if current['funding_pct'] < -0.15 and current['ls_ratio'] > 2.8:
                    bias = "BEARISH" 
                    insight = f"L/S {current['ls_ratio']:.1f} vs funding {current['funding_pct']:.2f}% shows retail crowded long while smart money shorts. Basis {current['basis_pct']:.2f}% confirms perp discount."
                    risk = f"Long liquidations above ${current['long_liq_24h']/1e6:.0f}M could cascade if price breaks support"
                    action = "Short rallies above current price, target breakdown levels"
                elif current['funding_pct'] > 0.1 and current['ls_ratio'] < 1.5:
                    bias = "BULLISH"
                    insight = f"Low L/S {current['ls_ratio']:.1f} with positive funding {current['funding_pct']:.2f}% shows shorts squeezed. OI {current['oi_24h_change']:+.1f}% suggests fresh positioning."
                    risk = f"Short squeeze risk if price breaks resistance"
                    action = "Long dips, target squeeze levels above current highs"
                else:
                    bias = "UNCLEAR"
                    insight = f"Mixed signals: L/S {current['ls_ratio']:.1f}, funding {current['funding_pct']:.2f}%, OI {current['oi_24h_change']:+.1f}% show conflicting forces"
                    risk = "Range-bound action with low conviction until clearer pattern emerges"
                    action = "Wait for breakout confirmation or positioning extremes"
                
                return f"""🎯 BIAS: {bias}
📊 KEY INSIGHT: {insight}
⚠️ TOP RISK: {risk}
💡 ACTION: {action}"""
                
            def format_whatsapp(self, analysis, data):
                """Test WhatsApp formatting"""
                header = f"🎯 SOL • 15:45 UTC\n"
                header += f"📊 ${data['price']:.2f} ({data['price_24h_change']:+.1f}% 24h) | OI: ${data['oi_usd']/1e6:.1f}M ({data['oi_24h_change']:+.1f}%)\n"
                header += f"💸 {data['funding_pct']:.3f}% → {data['predicted_funding_pct']:.3f}% | L/S: {data['ls_ratio']:.2f}\n\n"
                
                return header + analysis + "\n\n📈 Hourly + o3"
        
        analyzer = MockAnalyzer()
    
    # Test analysis
    analysis = analyzer.analyze_with_reasoning(mock_data)
    print("🧠 ANALYSIS RESULT:")
    print("-" * 40)
    print(analysis)
    print("-" * 40)
    print()
    
    # Test WhatsApp formatting
    whatsapp_msg = analyzer.format_whatsapp(analysis, mock_data)
    print("📱 WHATSAPP MESSAGE:")
    print("-" * 40)
    print(whatsapp_msg)
    print("-" * 40)
    print(f"Length: {len(whatsapp_msg)} characters")
    print()
    
    # Show the data structure
    print("📊 COMPREHENSIVE DATA STRUCTURE:")
    print(json.dumps(mock_data, indent=2))

if __name__ == "__main__":
    test_comprehensive_analysis()