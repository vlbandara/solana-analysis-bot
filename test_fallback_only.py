#!/usr/bin/env python3
"""
Test just the fallback analysis logic
"""

def generate_fallback_analysis(data):
    """Generate analysis with reasoning when o3 fails"""
    current_ls = data.get('current_ls_ratio', 0)
    avg_ls = data.get('avg_ls_ratio_24h', 0)
    funding = data.get('funding_rate_pct', 0)
    predicted_funding = data.get('predicted_funding_rate_pct', 0)
    price_change = data.get('price_change_24h_pct', 0)
    oi_change = data.get('oi_change_24h_pct', 0)
    current_price = data.get('current_price', 0)
    ls_change = data.get('ls_ratio_change_24h_pct', 0)
    
    # Enhanced logic-based analysis with reasoning
    if funding < -0.15 and current_ls > 2.5:
        bias = "BEARISH"
        reasoning = f"L/S {current_ls:.1f} (vs {avg_ls:.1f} avg) with funding {funding:.3f}% shows retail longs crowded while institutions short perps"
        insight = f"📊 KEY INSIGHT: {reasoning}. This divergence indicates smart money positioning against retail sentiment"
        risk = f"Long liquidation cascade below ${current_price * 0.97:.0f} as overleveraged longs get squeezed"
        action = f"Short bounces to ${current_price * 1.02:.0f}, target ${current_price * 0.95:.0f}. Logic: negative funding makes short carry profitable"
    elif funding > 0.1 and current_ls < 1.5:
        bias = "BULLISH"
        reasoning = f"Low L/S {current_ls:.1f} with positive funding {funding:.3f}% suggests shorts overextended and paying premium"
        insight = f"📊 KEY INSIGHT: {reasoning}. When shorts pay longs, it often precedes squeeze"
        risk = f"Short squeeze above ${current_price * 1.03:.0f} as funding costs force short covering"
        action = f"Buy dips to ${current_price * 0.98:.0f}, target ${current_price * 1.05:.0f}. Logic: positive funding rewards long positions"
    else:
        bias = "UNCLEAR" 
        reasoning = f"L/S {current_ls:.1f} vs funding {funding:.3f}% showing mixed signals"
        insight = f"📊 KEY INSIGHT: {reasoning}. Price +{price_change:.1f}% but OI only +{oi_change:.1f}% suggests cautious positioning"
        risk = f"Range-bound {current_price * 0.97:.0f}-{current_price * 1.03:.0f} until positioning clarifies"
        action = "Wait for funding/L/S alignment or clear breakout above/below range. Logic: conflicting signals need resolution"
    
    return f"""🎯 BIAS: {bias}
{insight}
⚠️ TOP RISK: {risk}
💡 ACTION: {action}"""

def format_for_whatsapp(analysis, data):
    """Format concise analysis for WhatsApp delivery"""
    from datetime import datetime, timezone
    
    header = f"🎯 SOL • {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n"
    header += f"📊 ${data.get('current_price', 0):.2f} | OI: ${data.get('open_interest_usd', 0)/1e6:.1f}M\n"
    header += f"💸 {data.get('funding_rate_pct', 0):.3f}% | L/S: {data.get('current_ls_ratio', 0):.2f}\n\n"
    
    footer = "\n📈 o3"
    
    return header + analysis + footer

def test_fallback():
    print("🔄 TESTING FALLBACK ANALYSIS")
    print("=" * 50)
    
    # Current SOL conditions (based on your last output)
    mock_data = {
        'current_price': 167.51,
        'price_change_24h_pct': 3.22,
        'open_interest_usd': 1520000000,  # $1.52B
        'oi_change_24h_pct': 0.55,
        'funding_rate_pct': -0.2117,
        'predicted_funding_rate_pct': -0.25,
        'current_ls_ratio': 3.01,
        'avg_ls_ratio_24h': 3.15,  # Slightly higher average
        'ls_ratio_change_24h_pct': -4.4,  # Declining L/S
        'long_liquidations_24h_usd': 2300000,  # $2.3M
        'short_liquidations_24h_usd': 2200000,  # $2.2M
    }
    
    print("📊 Mock data (matching your last run):")
    print(f"   Price: ${mock_data['current_price']:.2f} (+{mock_data['price_change_24h_pct']:.1f}%)")
    print(f"   Funding: {mock_data['funding_rate_pct']:.3f}%")
    print(f"   L/S Ratio: {mock_data['current_ls_ratio']:.2f}")
    print(f"   OI: ${mock_data['open_interest_usd']/1e6:.1f}M")
    
    # Generate analysis
    analysis = generate_fallback_analysis(mock_data)
    
    print(f"\n🧠 Generated analysis:")
    print("-" * 30)
    print(analysis)
    print("-" * 30)
    
    # Test WhatsApp format
    whatsapp_msg = format_for_whatsapp(analysis, mock_data)
    
    print(f"\n📱 WhatsApp format ({len(whatsapp_msg)} chars):")
    print("-" * 30)
    print(whatsapp_msg)
    print("-" * 30)
    
    if len(whatsapp_msg) > 1600:
        print("❌ Still too long for WhatsApp!")
    else:
        print("✅ WhatsApp compatible length!")
        
    # Test the logic
    print(f"\n🔍 Analysis logic:")
    funding = mock_data['funding_rate_pct']
    ls_ratio = mock_data['current_ls_ratio']
    
    print(f"   Funding: {funding:.3f}% ({'< -0.15' if funding < -0.15 else '>= -0.15'})")
    print(f"   L/S Ratio: {ls_ratio:.2f} ({'> 2.5' if ls_ratio > 2.5 else '<= 2.5'})")
    
    if funding < -0.15 and ls_ratio > 2.5:
        print("   → BEARISH logic triggered")
    else:
        print("   → NEUTRAL/OTHER logic")

if __name__ == "__main__":
    test_fallback()