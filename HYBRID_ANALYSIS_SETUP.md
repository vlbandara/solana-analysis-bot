# SOL Hybrid Analysis Workflow Setup

## Overview

This workflow runs hourly SOL analysis using a hybrid approach that combines:
- **Coinalyze API**: Precise derivatives data (funding rates, OI, liquidations, L/S ratios)
- **Sonar (via OpenRouter)**: Enhanced technical analysis and real-time news
- **WhatsApp Integration**: Automatic message sending via Twilio

## Workflow Details

- **Schedule**: Runs every hour at minute 10 (UTC)
- **File**: `.github/workflows/sol-hybrid-analysis.yml`
- **Script**: `sol_hybrid_analysis.py`

## Required GitHub Secrets

### API Keys
- `COINALYZE_API_KEY`: Your Coinalyze API key for derivatives data
- `OPENAI_API_KEY`: Your OpenRouter API key (used for Sonar model access)

### WhatsApp/Twilio Configuration
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_WHATSAPP_FROM`: Your Twilio WhatsApp number (format: +1234567890)
- `WHATSAPP_TO_NUMBER`: Recipient WhatsApp number (format: +1234567890)
- `WHATSAPP_TO_NUMBERS`: Multiple recipients (comma-separated)

### Optional OpenRouter Headers
- `OPENROUTER_REFERER`: Custom referer for API tracking (defaults to GitHub repo)
- `OPENROUTER_TITLE`: Custom title for API tracking (defaults to "SOL Hybrid Analysis")

## Analysis Features

### Derivatives Data (Coinalyze)
- Current price and 24h/6h changes
- Open Interest (OI) trends
- Funding rates (current and predicted)
- Long/Short ratios
- Liquidation data

### Technical Analysis (Sonar)
- Real-time chart analysis (1h & 4h timeframes)
- Supply/Demand zone identification
- Order block detection
- Liquidity zone mapping
- Fresh news from last 60 minutes only

### Output Format
```
🔥 SOL HYBRID ANALYSIS • HH:MM UTC
📊 $XX.XX (+X.X% 24h) | OI: $XX.XM | Funding: X.XXX%
============================================================

🚨 SIGNAL: [LONG|SHORT|WAIT]
📊 SETUP: [Brief technical + derivatives correlation]
📰 NEWS: [Recent news or 'None']
🎯 ENTRY: [Entry zone]
⛔ STOP: [Stop loss]
🎪 TARGET: [Target level]
⚠️ RISK: [Key risk]

============================================================
🔬 Hybrid: Coinalyze derivatives + Sonar technical analysis
📡 Real-time: Technical patterns + Fresh news (last hour)
🎯 Focus: WhatsApp trading updates
```

## Manual Triggering

You can manually trigger the workflow from the GitHub Actions tab with options:
- `send_whatsapp`: Toggle WhatsApp message sending (default: true)

## Monitoring

- **Artifacts**: Analysis logs and JSON files are archived for 7 days
- **WhatsApp**: Messages are sent automatically when `AUTO_SEND_TO_WHATSAPP=true`
- **Error Handling**: Failed runs are logged and artifacts are still saved

## Differences from Original Workflow

1. **Hybrid Approach**: Combines derivatives data with technical analysis
2. **Fresh News**: Only includes news from the last 60 minutes
3. **Enhanced Prompting**: More robust technical pattern recognition
4. **Actionable Insights**: Focuses on 3-5% move opportunities for spot trading
5. **Different Schedule**: Runs at minute 10 instead of minute 5 to avoid conflicts

## Troubleshooting

### Common Issues
1. **Missing API Keys**: Ensure all required secrets are set in GitHub
2. **WhatsApp Not Sending**: Check Twilio credentials and phone number format
3. **Analysis Failures**: Check OpenRouter API key and rate limits
4. **Empty Results**: Verify Coinalyze API key and data availability

### Debug Steps
1. Check workflow logs in GitHub Actions
2. Verify all environment variables are set
3. Test API keys manually
4. Check WhatsApp opt-in status for Twilio sandbox
