# 🎯 SOL Hourly Analysis Bot

Simple, robust hourly SOL derivatives analysis with WhatsApp alerts.

## 🚀 How It Works

**Every hour, the bot:**
1. 📊 Gets SOL data snapshot (price, OI, funding, L/S ratio)
2. 🔍 Compares with last analysis to detect significant changes
3. 🧠 Generates analysis with reasoning (using o3 model)
4. 📱 Sends WhatsApp alert only if changes are meaningful
5. 💾 Saves state to avoid duplicate messages

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
🎯 SOL • 15:30 UTC
📊 $167.51 | OI: $1.52M
💸 -0.212% | L/S: 3.01

🎯 BIAS: BEARISH
📊 KEY INSIGHT: L/S 3.0 vs funding -0.212% shows retail longs 
crowded while institutions short perps. Smart money vs retail.
⚠️ TOP RISK: Long cascade below $162 as overleveraged exit
💡 ACTION: Short bounces to $171, target $159. Negative 
funding makes carry profitable.

📈 Hourly
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

---

**Simple. Robust. No complexity. Just works. 🎯**
