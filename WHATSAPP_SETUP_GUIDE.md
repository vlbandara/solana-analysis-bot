# 📱 WhatsApp Integration Setup Guide

## 🎯 OPTION 1: Twilio WhatsApp API (RECOMMENDED)

### Step 1: Get Twilio Account (FREE TRIAL)
1. Go to [twilio.com](https://twilio.com)
2. Sign up for free account
3. Get your **Account SID** and **Auth Token**
4. Get a **WhatsApp-enabled phone number** (free trial available)

### Step 2: Install Twilio
```bash
uv add twilio
```

### Step 3: Set Environment Variables
Add to your `.env` file:
```bash
# Twilio WhatsApp (MUCH EASIER!)
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Your Twilio WhatsApp number
WHATSAPP_TO_NUMBER=whatsapp:+1234567890  # Recipient's WhatsApp number

# For groups (send to multiple numbers)
WHATSAPP_GROUP_NUMBERS=+1234567890,+0987654321,+1122334455
```

### Step 4: Test Twilio Integration
```bash
uv run python twilio_whatsapp_setup.py
```

## 🎯 OPTION 2: WhatsApp Web Automation (Alternative)

### Step 1: Install Dependencies
```bash
uv add selenium webdriver-manager
```

### Step 2: Set Group Name
```bash
export WHATSAPP_GROUP_NAME="Your WhatsApp Group Name"
```

### Step 3: Run Analysis + Send
```bash
# First run your analysis
uv run python o3_enhanced_solana_agent.py

# Then send to WhatsApp group
uv run python whatsapp_selenium.py
```

### Step 4: Scan QR Code
1. A Chrome browser will open automatically
2. Scan the QR code with your phone's WhatsApp
3. The script will automatically find your group and send the message

## 🎯 OPTION 3: Manual Copy-Paste (Easiest)

### Step 1: Run Analysis
```bash
uv run python o3_enhanced_solana_agent.py
```

### Step 2: Copy Output
Copy this part from the terminal:
```
🔔 SOL HOURLY BRIEF

Logic:
• Orderflow: 6.4× bid/ask depth & 137× B/S flow show aggressive dip-buying near $165-167
• Technical: MACD bullish div but still sub-zero; RSI 42.6 suggests room up; price hugging VWAP
• Derivatives/Funding: OI elevated, L/S 2.9 → long-crowded; flat funding masks squeeze risk
• On-chain: normal whale activity; flows neutral
• Risk/opp: strong bids & bullish div favor bounce to $170, but crowded longs could spur whipsaw

Long holders: Guard profits with tight stops; crowded longs make flash wicks likely 📉

Short holders: Fade rallies only near $170+; beware bid wall at $165 and rising momentum

Entry hunters: Watch $164.6-165.2 support cluster for low-risk entries; cut if $164 cracks

5-min scalp: LONG $165.40→$168.90 | SL $164.20 (risk: deep bid stack + bullish div near support)

Note: Volume 27.7× avg adds conviction; expect fast moves once $170 liquidity is tested
```

### Step 3: Paste into WhatsApp
- Open WhatsApp
- Go to your group
- Paste the copied text
- Send!

## 🚀 GitHub Actions Integration

### For GitHub Actions (Cloud Deployment):
Add these secrets to your GitHub repository:

```
TWILIO_ACCOUNT_SID = your_twilio_account_sid
TWILIO_AUTH_TOKEN = your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER = whatsapp:+14155238886
WHATSAPP_TO_NUMBER = whatsapp:+1234567890
WHATSAPP_GROUP_NUMBERS = +1234567890,+0987654321
```

## 💡 RECOMMENDATION

**Use Twilio WhatsApp API** because:
- ✅ Works in GitHub Actions (cloud)
- ✅ No browser needed
- ✅ Free trial available
- ✅ Reliable and professional
- ✅ Easy to set up

Your analysis will be sent automatically every hour! 🎯
