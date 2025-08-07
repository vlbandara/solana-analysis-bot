# Twilio WhatsApp Template Setup Guide

## Overview
This guide will help you create a Twilio WhatsApp template for your SOL analysis messages. The template will make your messages more professional and consistent.

## Step 1: Access Twilio Console

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Content Editor** → **Templates**
3. Click **Create Template**

## Step 2: Template Configuration

### Template Details
- **Template Name:** `sol_analysis_update`
- **Category:** Marketing
- **Language:** English
- **Status:** Submit for approval

### Template Content
```
🚨 SIGNAL: {{1}}

📊 SETUP: {{2}}

📰 NEWS: {{3}}

🎯 ENTRY: {{4}}

⛔ STOP: {{5}}

🎪 TARGET: {{6}}

⚠️ RISK: {{7}}
```

### Template Variables
1. `{{1}}` - Signal (LONG/SHORT/WAIT)
2. `{{2}}` - Setup description
3. `{{3}}` - News (or "None")
4. `{{4}}` - Entry zone
5. `{{5}}` - Stop loss
6. `{{6}}` - Target level
7. `{{7}}` - Key risk

## Step 3: Environment Variables

Add these to your `.env` file:

```bash
# Twilio Template
TWILIO_TEMPLATE_SID=HX...  # Your template SID from Twilio
```

## Step 4: Template Approval Process

### What to Expect
1. **Submission:** Template will be in "Pending" status
2. **Review:** Twilio reviews for compliance (24-48 hours)
3. **Approval:** Template becomes "Approved" and ready to use

### Common Approval Issues
- **Emojis:** Most emojis are approved, but some may be rejected
- **Trading terms:** Avoid terms like "guaranteed returns" or "risk-free"
- **Financial advice:** Include disclaimers if needed

## Step 5: Testing the Template

### Test Message Structure
Your analysis should produce messages like this:

```
🚨 SIGNAL: LONG (Short-term)

📊 SETUP: SOL recovering from $168-171 demand zone with declining OI (-1.1% 24h) while price rises (+1.1%) - classic short covering pattern. Long/short ratio dropped to 2.69 from 2.79 average, yet $1.7M shorts liquidated vs only $0.7M longs. Price approaching key supply zone at $175 where previous rejections occurred.

📰 NEWS: None (last 60 minutes)

🎯 ENTRY: $170-172 (current level)

⛔ STOP: $167.50 (below demand zone)

🎪 TARGET: $175 (first resistance), $180 (extended)

⚠️ RISK: Heavy resistance at $175 level where price previously rejected. Declining OI suggests weak conviction - could reverse quickly if shorts stop covering.
```

## Step 6: Code Integration

The updated code will automatically:
1. Parse your analysis message
2. Extract template variables
3. Send using the template if available
4. Fall back to direct message if template fails

### Template Variable Mapping
- **Signal:** Extracts from "🚨 SIGNAL:" line
- **Setup:** Extracts multi-line setup description
- **News:** Extracts from "📰 NEWS:" line
- **Entry:** Extracts from "🎯 ENTRY:" line
- **Stop:** Extracts from "⛔ STOP:" line
- **Target:** Extracts from "🎪 TARGET:" line
- **Risk:** Extracts from "⚠️ RISK:" line

## Step 7: Verification

### Test the Integration
1. Set `AUTO_SEND_TO_WHATSAPP=true` in your `.env`
2. Run your analysis: `python sol_hybrid_analysis.py`
3. Check WhatsApp for the formatted message

### Debug Information
The code will show:
- Template variable parsing results
- Template SID usage
- Delivery status

## Troubleshooting

### Common Issues

1. **Template Not Found**
   ```
   ❌ Template SID not found
   ```
   - Verify `TWILIO_TEMPLATE_SID` in `.env`
   - Check template approval status

2. **Variable Parsing Failed**
   ```
   ⚠️ Missing template variables
   ```
   - Check analysis message format
   - Ensure all required sections are present

3. **Delivery Failed**
   ```
   ⚠️ Message not delivered
   ```
   - Verify WhatsApp opt-in
   - Check template approval status
   - Review Twilio logs

### Fallback Behavior
- If template fails, falls back to direct message
- If parsing fails, sends full analysis as-is
- Maintains functionality even without template

## Benefits of Using Templates

1. **Consistency:** All messages follow same format
2. **Professional:** Clean, structured appearance
3. **Compliance:** Pre-approved content structure
4. **Reliability:** Better delivery rates
5. **Branding:** Consistent with your trading style

## Next Steps

1. Create the template in Twilio Console
2. Wait for approval (24-48 hours)
3. Add template SID to `.env`
4. Test with your analysis
5. Monitor delivery success rates

## Support

If you encounter issues:
1. Check Twilio Console logs
2. Verify template approval status
3. Test with simple messages first
4. Contact Twilio support if needed
