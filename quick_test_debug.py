#!/usr/bin/env python3
"""
Quick test to debug o3 response issues
"""

import os
from single_o3_solana_agent import SingleO3SolanaAgent

def test_o3_response():
    """Test what o3 is actually returning"""
    
    print("🔍 DEBUGGING O3 RESPONSE ISSUES")
    print("=" * 50)
    
    # Create mock data for testing
    mock_data = {
        'current_price': 167.51,
        'price_change_24h_pct': 3.22,
        'open_interest_usd': 1520000000,
        'oi_change_24h_pct': 0.55,
        'funding_rate_pct': -0.2117,
        'current_ls_ratio': 3.01,
        'long_liquidations_24h_usd': 2300000,
        'short_liquidations_24h_usd': 2200000,
        'patterns': {}
    }
    
    print("📊 Mock data prepared:")
    print(f"   Price: ${mock_data['current_price']:.2f}")
    print(f"   Funding: {mock_data['funding_rate_pct']:.3f}%") 
    print(f"   L/S: {mock_data['current_ls_ratio']:.2f}")
    
    try:
        print("\n🧠 Testing o3 analysis...")
        agent = SingleO3SolanaAgent()
        analysis = agent.analyze_with_o3(mock_data)
        
        print(f"\n✅ Analysis received:")
        print(f"Length: {len(analysis)} characters")
        print("Content:")
        print("-" * 30)
        print(analysis)
        print("-" * 30)
        
        # Test WhatsApp format
        whatsapp_msg = agent.format_for_whatsapp(analysis, mock_data)
        print(f"\n📱 WhatsApp format ({len(whatsapp_msg)} chars):")
        print("-" * 30)
        print(whatsapp_msg)
        print("-" * 30)
        
        if len(whatsapp_msg) > 1600:
            print("❌ Still too long for WhatsApp!")
        else:
            print("✅ WhatsApp compatible length!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ OPENAI_API_KEY not set - set it to test o3 responses")
        print("For now, testing fallback analysis...")
        
        agent = SingleO3SolanaAgent()
        mock_data = {
            'current_price': 167.51,
            'funding_rate_pct': -0.2117,
            'current_ls_ratio': 3.01,
        }
        
        fallback = agent._generate_fallback_analysis(mock_data)
        print("\n🔄 Fallback analysis:")
        print("-" * 30)
        print(fallback)
        print("-" * 30)
    else:
        test_o3_response()