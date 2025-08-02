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
    As of January 2025, provide a detailed technical and fundamental analysis of Solana (SOL) cryptocurrency with specific trading recommendations:

    **CRITICAL REQUIREMENTS - Must provide specific numbers:**

    1. **CURRENT MARKET DATA** (analyze as if SOL is trading around $200-220):
       - Assess current price momentum and trend direction
       - Open Interest trends in derivatives markets
       - Long/Short ratio analysis from major exchanges
       - Volume patterns and institutional flow
       - Key support levels: $X, $Y, $Z
       - Key resistance levels: $A, $B, $C

    2. **TECHNICAL ANALYSIS**:
       - RSI levels and overbought/oversold conditions
       - MACD signal and crossover analysis
       - 20/50/200 EMA analysis and positioning
       - Fibonacci levels for retracements and extensions
       - Chart patterns (triangles, flags, head & shoulders)

    3. **FUNDAMENTAL CATALYSTS**:
       - Network growth metrics and TVL trends
       - Recent ecosystem developments
       - Upcoming events or upgrades
       - Regulatory environment impact

    4. **SPECIFIC TRADING SETUP** (Must provide exact numbers):
       - **POSITION TYPE**: LONG or SHORT (choose one and explain)
       - **ENTRY ZONE**: $X.XX - $Y.YY (specific price range)
       - **TARGET 1**: $Z.ZZ (first profit target)
       - **TARGET 2**: $A.AA (second profit target) 
       - **TARGET 3**: $B.BB (final target)
       - **STOP LOSS**: $C.CC (risk management level)
       - **POSITION SIZE**: X% of portfolio
       - **TIME HORIZON**: X days/weeks/months
       - **RISK/REWARD RATIO**: 1:X

    5. **RISK MANAGEMENT**:
       - Maximum drawdown expectations
       - Alternative scenarios if trade fails
       - Market conditions that would invalidate the setup

    **FORMAT REQUIREMENT**: Present as a professional trading report with specific price levels. Assume SOL current price is around $200-220 and provide realistic targets based on technical levels.
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
                    "content": "You are a world-class cryptocurrency trader and quantitative analyst with 20+ years of experience in traditional finance and digital assets. Use advanced technical analysis, market microstructure knowledge, derivatives analysis, and comprehensive risk management. Provide detailed, actionable trading strategies with precise entry points, multiple profit targets, and sophisticated stop-loss management. Consider macro factors, on-chain metrics, and market sentiment in your analysis."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            max_completion_tokens=8000  # Using max_completion_tokens for full o3 model
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
                            "content": "You are an expert cryptocurrency trader with 15+ years experience. Provide concrete trading recommendations with specific entry points, targets, and stop losses. Do not give generic advice - provide actionable trading setups with exact price levels. Assume you have access to current market data and analysis tools."
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.1  # Lower temperature for more focused analysis
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