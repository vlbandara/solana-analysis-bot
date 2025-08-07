#!/usr/bin/env python3
"""
Sonar Experiment: Let Sonar browse and find SOL derivatives data independently
Test Sonar's real-time browsing capabilities for crypto analysis without Coinalyze
"""
import os
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SonarSOLExperiment:
    """Experimental SOL analysis using only Sonar's browsing capabilities."""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY required")
    
    def analyze_sol_with_sonar_browsing(self) -> str:
        """Let Sonar browse and analyze SOL derivatives data independently."""
        
        client = OpenAI(
            api_key=self.openai_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Enhanced prompt for Sonar to browse and find data
        prompt = (
            "TASK: Comprehensive SOL (Solana) derivatives analysis for intraday spot trading\n\n"
            
            "INSTRUCTIONS:\n"
            "1. Browse and find CURRENT real-time data for SOL perpetual futures:\n"
            "   - Current SOL price and 24h change\n"
            "   - Open Interest (OI) in USD and recent changes\n"
            "   - Funding rates (current and predicted) from major exchanges\n"
            "   - Long/Short ratios and liquidation data\n"
            "   - Recent price action and key levels\n\n"
            
            "2. Browse for macro context:\n"
            "   - Bitcoin dominance percentage\n"
            "   - DXY (Dollar Index) current value\n"
            "   - Any major crypto news affecting SOL in last 2 hours\n\n"
            
            "3. Analyze for SHORT-TERM (3-5% moves) spot trading opportunities:\n"
            "   - Focus on derivatives-driven signals (funding stress, OI divergences)\n"
            "   - Identify bounce/drop setups based on liquidation patterns\n"
            "   - Consider leverage stress points and funding cycle impacts\n"
            "   - Look for squeeze setups or distribution signals\n\n"
            
            "4. Provide actionable insights for SOL spot buy/sell decisions\n\n"
            
            "RESPONSE FORMAT (copy exactly):\n"
            "🔍 DATA SOURCES: <List the specific sites/sources you browsed>\n"
            "📊 SOL SNAPSHOT:\n"
            "• Price: $X.XX (+X.X% 24h)\n"
            "• OI: $XXXXMs (change %)\n" 
            "• Funding: X.XXX% → X.XXX% (pred)\n"
            "• L/S Ratio: X.XX\n"
            "• BTC Dom: XX.X% | DXY: XXX.X\n\n"
            
            "🚨 SIGNAL: <PUMP RISK|DROP RISK|SQUEEZE SETUP|DISTRIBUTION|NO CLEAR SIGNAL>\n"
            "📈 CORRELATION: <Key relationships between funding, OI, liquidations, macro>\n"
            "📰 NEWS: <Recent major news affecting SOL or 'None'>\n"
            "⚠️ POSITIONED: <Specific warnings for longs/shorts with price levels>\n"
            "💡 PREPARE: <Actionable strategy for 3-5% move with entry/exit levels>\n\n"
            
            "CRITICAL: Use your browsing capabilities to find the most current data. "
            "Focus on derivatives exchanges like Binance, OKX, Bybit for futures data. "
            "Check CoinGlass, CoinGecko, or similar for comprehensive metrics."
        )
        
        system_prompt = (
            "You are an elite cryptocurrency derivatives analyst with real-time market access. "
            "Use your browsing capabilities to gather the most current SOL perpetual futures data "
            "from multiple sources. Focus on actionable insights for short-term spot trading. "
            "Always browse for fresh data rather than relying on training knowledge. "
            "Be thorough in your data collection and precise in your analysis."
        )
        
        print("🧠 Starting Sonar browsing experiment...")
        print("🔍 Letting Sonar find SOL derivatives data independently...")
        
        try:
            response = client.chat.completions.create(
                model="perplexity/sonar-reasoning-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                extra_headers={
                    "HTTP-Referer": "https://github.com/sol-analysis-tool",
                    "X-Title": "SOL Derivatives Analysis Experiment",
                }
            )
            
            analysis = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            
            if not analysis:
                raise RuntimeError("Empty response from Sonar")
                
            print(f"✅ Sonar analysis complete ({len(analysis)} chars)")
            return analysis
            
        except Exception as exc:
            print(f"❌ Sonar experiment failed: {exc}")
            return (
                "🔍 DATA SOURCES: Unable to browse due to technical issues\n"
                "🚨 SIGNAL: NO CLEAR SIGNAL\n"
                "📈 CORRELATION: Analysis unavailable\n"
                "📰 NEWS: Unable to check\n"
                "⚠️ POSITIONED: Monitor manually\n"
                "💡 PREPARE: Use backup data sources"
            )
    
    def format_result(self, analysis: str) -> str:
        """Format the result with timestamp and experiment info."""
        utc_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        header = (
            f"🧪 SONAR EXPERIMENT • {utc_time}\n"
            f"🎯 SOL Analysis via Independent Browsing\n"
            f"{'='*50}\n\n"
        )
        
        footer = (
            f"\n{'='*50}\n"
            f"🔬 Experiment: Sonar browsing vs Coinalyze API\n"
            f"📡 Model: perplexity/sonar-reasoning-pro"
        )
        
        return header + analysis + footer
    
    def run_experiment(self):
        """Run the complete Sonar browsing experiment."""
        print("🧪 SOL Sonar Browsing Experiment Starting...")
        print("🎯 Testing Sonar's independent data discovery capabilities")
        print("-" * 60)
        
        analysis = self.analyze_sol_with_sonar_browsing()
        formatted_result = self.format_result(analysis)
        
        print("\n📋 EXPERIMENT RESULTS:")
        print("=" * 60)
        print(formatted_result)
        print("=" * 60)
        
        return formatted_result

def main():
    """Run the Sonar experiment."""
    try:
        experiment = SonarSOLExperiment()
        experiment.run_experiment()
    except Exception as e:
        print(f"❌ Experiment failed: {e}")

if __name__ == "__main__":
    main()

