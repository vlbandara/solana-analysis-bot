#!/usr/bin/env python3
"""
Enhanced Sonar Experiment: More specific guidance for finding SOL derivatives data
"""
import os
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SonarSOLExperimentV2:
    """Enhanced SOL analysis with more specific browsing instructions."""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required")
    
    def analyze_sol_enhanced(self) -> str:
        """Enhanced Sonar analysis with specific data source guidance."""
        
        client = OpenAI(
            api_key=self.openai_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # More specific prompt with exact sites to check
        prompt = (
            "URGENT SOL DERIVATIVES ANALYSIS NEEDED\n\n"
            
            "SPECIFIC SITES TO CHECK (browse these exact URLs/sites):\n"
            "1. CoinGlass.com - For SOL perpetual futures funding rates, OI, liquidations\n"
            "2. Binance SOL-USDT perpetual futures page - Current funding rate\n"
            "3. Coingecko.com SOL page - Current price, 24h change\n"
            "4. TradingView SOL/USDT - Technical levels, recent price action\n"
            "5. Alternative.me crypto fear/greed index\n"
            "6. Any recent SOL news from CoinDesk, CryptoPanic, or Decrypt\n\n"
            
            "CRITICAL DATA TO FIND:\n"
            "• SOL current price and 24h percentage change\n"
            "• Binance SOL perpetual funding rate (current and next)\n"
            "• Open Interest in SOL futures (USD value if possible)\n"
            "• Recent liquidations (long vs short)\n"
            "• Long/Short ratio from any major exchange\n"
            "• Key technical levels (support/resistance)\n"
            "• BTC dominance percentage\n"
            "• Any breaking SOL news in last 2 hours\n\n"
            
            "ANALYSIS FOCUS:\n"
            "Based on the derivatives data you find, identify:\n"
            "- Funding rate stress (high positive = long squeeze risk)\n"
            "- OI divergences with price (bearish if OI drops with price rise)\n"
            "- Liquidation imbalances (more longs liquidated = potential bounce)\n"
            "- Technical support/resistance for entry/exit levels\n\n"
            
            "OUTPUT FORMAT:\n"
            "🌐 BROWSED SOURCES: <List specific sites you checked>\n"
            "💰 SOL PRICE: $XXX.XX (+/-X.X% 24h)\n"
            "📊 DERIVATIVES:\n"
            "  • Funding: X.XXX% (next: X.XXX%)\n"
            "  • Open Interest: $XXXXMs\n"
            "  • Liquidations: $XXM longs / $XXM shorts\n"
            "  • L/S Ratio: X.XX\n"
            "🌍 MACRO: BTC Dom: XX.X%\n"
            "📰 NEWS: <Any breaking SOL news or 'None'>\n\n"
            
            "🚨 SIGNAL: <BULLISH|BEARISH|NEUTRAL>\n"
            "🎯 STRATEGY: <Specific entry/exit levels for 3-5% move>\n"
            "⚠️ RISK: <Key levels to watch>\n\n"
            
            "BE THOROUGH: Actually visit these sites and extract real numbers. "
            "Don't give generic responses - find the actual current data!"
        )
        
        system_prompt = (
            "You are a professional crypto derivatives trader who needs real-time data. "
            "Use your browsing capabilities to visit the specific websites mentioned. "
            "Extract exact numbers, not approximations. Focus on actionable trading insights. "
            "If you can't find specific data from a source, clearly state what you couldn't access."
        )
        
        print("🧠 Enhanced Sonar experiment with specific site guidance...")
        
        try:
            response = client.chat.completions.create(
                model="perplexity/sonar-reasoning-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/sol-analysis-tool",
                    "X-Title": "SOL Enhanced Derivatives Analysis",
                }
            )
            
            analysis = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            
            if not analysis:
                raise RuntimeError("Empty response from Sonar")
                
            print(f"✅ Enhanced Sonar analysis complete ({len(analysis)} chars)")
            return analysis
            
        except Exception as exc:
            print(f"❌ Enhanced experiment failed: {exc}")
            return f"❌ Error: {exc}"
    
    def run_enhanced_experiment(self):
        """Run the enhanced experiment."""
        print("🧪 SOL Enhanced Sonar Experiment Starting...")
        print("🎯 Testing specific site guidance for derivatives data")
        print("-" * 60)
        
        analysis = self.analyze_sol_enhanced()
        
        utc_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        result = (
            f"🧪 ENHANCED SONAR EXPERIMENT • {utc_time}\n"
            f"🎯 SOL Analysis with Specific Site Guidance\n"
            f"{'='*60}\n\n"
            f"{analysis}\n\n"
            f"{'='*60}\n"
            f"🔬 V2 Experiment: Specific browsing instructions\n"
            f"📡 Model: perplexity/sonar-reasoning-pro"
        )
        
        print("\n📋 ENHANCED EXPERIMENT RESULTS:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        return result

def main():
    """Run the enhanced experiment."""
    try:
        experiment = SonarSOLExperimentV2()
        experiment.run_enhanced_experiment()
    except Exception as e:
        print(f"❌ Enhanced experiment failed: {e}")

if __name__ == "__main__":
    main()

