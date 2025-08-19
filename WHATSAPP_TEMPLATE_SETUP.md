# WhatsApp Template Setup Guide

## 🚨 **IMPORTANT: Template Required for Business Messages**

WhatsApp requires using **Message Templates** for business-initiated messages. Freeform messages are only allowed within a 24-hour customer service window.

## 📋 **Required Environment Variable**

```bash
TWILIO_TEMPLATE_SID=your_template_sid_here
```

## 🔧 **How to Create a Template in Twilio**

### Step 1: Access Twilio Console
1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Templates** → **WhatsApp Templates**

### Step 2: Create New Template
1. Click **Create Template**
2. Select **WhatsApp** as platform
3. Choose **Business-Initiated** message type

### Step 3: Template Content
Use this exact template structure:

```
🎯 SOL • {{1}} UTC
📊 ${{2}} ({{3}}% 24h) | OI: ${{4}}M ({{5}}%)
💸 {{6}}% → {{7}}% | L/S: {{8}}

🚨 SIGNAL: {{9}}
📊 CORRELATION: {{10}}
⚠️ POSITIONED: {{11}}
💡 PREPARE: {{12}}

📈 24h evolution • o3
```

### Step 4: Template Variables
Add these 12 variables:
- `{{1}}` - Time (UTC)
- `{{2}}` - Price
- `{{3}}` - 24h Change %
- `{{4}}` - OI (Millions)
- `{{5}}` - OI Change %
- `{{6}}` - Funding Rate %
- `{{7}}` - Funding Change %
- `{{8}}` - L/S Ratio
- `{{9}}` - Signal
- `{{10}}` - Correlation
- `{{11}}` - Positioned
- `{{12}}` - Prepare

### Step 5: Submit for Approval
1. Submit template for WhatsApp approval
2. Wait for approval (usually 24-48 hours)
3. Copy the **Template SID** once approved

## 🔑 **Set Environment Variable**

```bash
# Add to your .env file
TWILIO_TEMPLATE_SID=HX1234567890abcdef1234567890abcdef

# Or set in GitHub Secrets for Actions
TWILIO_TEMPLATE_SID: HX1234567890abcdef1234567890abcdef
```

## ✅ **Verification**

Once set up, your workflow will:
1. ✅ Use approved template format
2. ✅ Send business-initiated messages
3. ✅ Avoid "outside allowed window" errors
4. ✅ Deliver messages successfully

## 🆘 **Troubleshooting**

- **Error 63016**: Template SID not configured
- **Undelivered messages**: Check template approval status
- **Missing variables**: Ensure all 12 variables are defined in template

## 📱 **Template Preview**

Your messages will look exactly like this:
```
🎯 SOL • 08:40 UTC
📊 $98.45 (+2.3% 24h) | OI: $156.7M (+1.8%)
💸 0.045% → +0.012% | L/S: 2.34

🚨 SIGNAL: LONG
📊 CORRELATION: Price above key resistance with OI support
⚠️ POSITIONED: High confidence setup
💡 PREPARE: Prepare entry zones

📈 24h evolution • o3
```