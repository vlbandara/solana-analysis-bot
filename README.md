# 🎯 SOL Hourly Analysis Bot

Simple, robust hourly SOL derivatives analysis with WhatsApp alerts.

## 🚀 How It Works

**Every hour, the bot:**
1. 📊 Gets comprehensive SOL data (15+ metrics with 24h patterns)
2. 🔍 Compares with last analysis to detect significant changes
3. 🧠 Generates rich analysis with reasoning (using o3 model)
4. 📱 Sends WhatsApp alert only if changes are meaningful
5. 💾 Saves state to avoid duplicate messages
6. 🛡️ Robust error handling continues even if some APIs fail

## 📁 Core Files

- **`sol_hourly_analysis.py`** - Main analysis script (simple & robust)
- **`whatsapp_sender.py`** - WhatsApp integration via Twilio
- **`.github/workflows/solana-analysis.yml`** - Automated hourly runs

## 🔧 Environment Variables

```bash
# Required
COINALYZE_API_KEY="your_key"
OPENAI_API_KEY="your_key"
TWILIO_ACCOUNT_SID="your_sid"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
WHATSAPP_TO_NUMBER="whatsapp:+1234567890"

# Optional
AUTO_SEND_TO_WHATSAPP="true"
```

## 🎯 Smart Alert Logic

**Only sends WhatsApp when:**
- Price moves >2%
- Open Interest changes >5%
- Funding rate shifts >0.05%
- L/S ratio changes >10%
- Or 4+ hours since last alert

**No spam, only meaningful updates! 📱**

## 📊 Analysis Format

```
🎯 SOL • 15:45 UTC
📊 $163.55 (-2.3% 24h) | OI: $1498.5M (+3.2%)
💸 -0.212% → -0.267% | L/S: 3.22

🎯 BIAS: BEARISH
📊 KEY INSIGHT: L/S 3.2 vs funding -0.21% shows retail crowded 
long while smart money shorts. Basis -0.04% confirms perp discount.
⚠️ TOP RISK: Long liquidations above $8M could cascade if price 
breaks support
💡 ACTION: Short rallies above current price, target breakdown levels

📈 Hourly + o3
```

## 🚀 Usage

**Local testing:**
```bash
python sol_hourly_analysis.py
```

**Production:**
- Runs automatically every hour via GitHub Actions
- State persists between runs to avoid duplicates
- Robust error handling with fallback analysis

## 🧠 Analysis Logic

- **BEARISH**: High L/S + negative funding = crowded longs
- **BULLISH**: Low L/S + positive funding = oversold shorts  
- **UNCLEAR**: Mixed signals need more clarity

**Reasoning included:** Shows WHY each conclusion was reached.

## 🛡️ Robust Error Handling

**Production-ready reliability:**
- ✅ Individual API calls wrapped in try/catch blocks
- ✅ Continues analysis even if some data sources fail
- ✅ Flexible field parsing (handles different API response formats)
- ✅ Meaningful error messages for debugging
- ✅ Fallback analysis when o3 model fails
- ✅ Never crashes, always provides some analysis

**Result: Works in production even with API hiccups! 🚀**

---

**Simple. Robust. Comprehensive. Just works. 🎯**
