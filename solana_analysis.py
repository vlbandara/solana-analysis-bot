#!/usr/bin/env python3
"""
Solana Analysis using ChatGPT o3 Model
Analyzes Solana with OpenInterest, ShortInterest, LongInterest metrics
Provides target prices, stop losses, and entry points
"""

import os
from openai import OpenAI

def analyze_solana():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Comprehensive query for Solana analysis
    query = """
    Please provide a comprehensive technical and fundamental analysis of Solana (SOL) cryptocurrency with the following specific requirements:

    1. MARKET ANALYSIS:
       - Current price action and trend analysis
       - Open Interest analysis and what it indicates
       - Short Interest vs Long Interest ratio analysis
       - Volume analysis and market sentiment
       - Support and resistance levels

    2. TECHNICAL INDICATORS:
       - RSI, MACD, Moving Averages analysis
       - Fibonacci retracement levels
       - Bollinger Bands analysis
       - Key chart patterns

    3. FUNDAMENTAL ANALYSIS:
       - Network activity and TVL (Total Value Locked)
       - Developer activity and ecosystem growth
       - Recent partnerships or developments
       - Market cap and tokenomics

    4. TRADING RECOMMENDATION:
       - Determine if this is a LONG or SHORT opportunity
       - Provide specific entry points with reasoning
       - Set target prices (multiple targets if applicable)
       - Define stop-loss levels with risk management
       - Position sizing recommendations
       - Time horizon for the trade

    5. RISK ASSESSMENT:
       - Market risks and potential catalysts
       - Risk-reward ratio analysis
       - Alternative scenarios (bull/bear cases)

    Please be specific with price levels and provide clear reasoning for each recommendation. Consider current market conditions, regulatory environment, and any upcoming events that might affect SOL price.
    """

    try:
        print("🔍 Analyzing Solana (SOL) using ChatGPT o3 model...")
        print("=" * 80)
        
        # Make API call to o3 model
        response = client.chat.completions.create(
            model="o3",  # Using full o3 model
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert cryptocurrency trader and analyst with deep knowledge of technical analysis, market microstructure, and risk management. Provide actionable trading insights with specific price levels."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            max_tokens=4000,
            temperature=0.3  # Lower temperature for more focused analysis
        )
        
        # Extract and display the analysis
        analysis = response.choices[0].message.content
        
        print("\n📊 SOLANA (SOL) COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(analysis)
        print("\n" + "=" * 80)
        print("⚠️  DISCLAIMER: This is AI-generated analysis for educational purposes.")
        print("💡 Always do your own research and manage risk appropriately.")
        print("🚨 Never invest more than you can afford to lose.")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error occurred during analysis: {str(e)}")
        if "invalid" in str(e).lower() and "model" in str(e).lower():
            print("ℹ️  Note: o3 model might not be available. Trying with gpt-4 instead...")
            try:
                # Fallback to GPT-4 if o3 is not available
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert cryptocurrency trader and analyst with deep knowledge of technical analysis, market microstructure, and risk management. Provide actionable trading insights with specific price levels."
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.3
                )
                
                analysis = response.choices[0].message.content
                print("\n📊 SOLANA (SOL) COMPREHENSIVE ANALYSIS (GPT-4)")
                print("=" * 80)
                print(analysis)
                print("\n" + "=" * 80)
                print("⚠️  DISCLAIMER: This is AI-generated analysis for educational purposes.")
                print("💡 Always do your own research and manage risk appropriately.")
                print("🚨 Never invest more than you can afford to lose.")
                
                return analysis
                
            except Exception as fallback_error:
                print(f"❌ Fallback error: {str(fallback_error)}")
                return None
        
        return None

if __name__ == "__main__":
    print("🚀 Starting Solana Analysis...")
    
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not found!")
        print("Please make sure you have set the API key in your environment.")
        exit(1)
    
    # Run the analysis
    result = analyze_solana()
    
    if result:
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n❌ Analysis failed. Please check your API key and try again.")