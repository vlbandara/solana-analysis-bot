# GitHub Secrets Setup for SOL Analysis

## Required Secrets

Navigate to your GitHub repository → Settings → Secrets and variables → Actions, then add these secrets:

### Mandatory Secrets
```
COINALYZE_API_KEY=your_coinalyze_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Optional WhatsApp Secrets
Only needed if you want automated WhatsApp notifications:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886
WHATSAPP_TO_NUMBER=+1234567890
```

## Workflow Behavior

### Scheduled Runs
- Runs automatically every hour at 5 minutes past (UTC)
- WhatsApp sending is **disabled** by default for scheduled runs
- Analysis results are logged and available in GitHub Actions

### Manual Runs
- Go to Actions → SOL 24h Evolution Analysis → Run workflow
- Choose whether to send WhatsApp notifications
- Useful for testing or immediate analysis

## Local vs GitHub Actions

### Local Development (.env file)
```bash
# Your .env file (not committed to git)
COINALYZE_API_KEY=your_key
OPENAI_API_KEY=your_key
AUTO_SEND_TO_WHATSAPP=false  # Keep disabled during dev
```

### GitHub Actions (Secrets)
- Uses GitHub repository secrets
- Same environment variable names
- Controlled WhatsApp sending via workflow inputs

## Security Notes

1. **Never commit API keys** to git
2. **.env files are gitignored** - they stay local
3. **GitHub secrets are encrypted** and only available during workflow runs
4. **WhatsApp is opt-in** for scheduled runs to prevent spam

## Testing the Workflow

1. Add the required secrets to your GitHub repository
2. Push this code to GitHub
3. Go to Actions → Run workflow manually
4. Check the logs for successful execution

## Troubleshooting

- If analysis fails, check the GitHub Actions logs
- Verify all required secrets are set correctly
- For WhatsApp issues, ensure your Twilio sandbox is configured
- For API issues, check your Coinalyze/OpenAI quotas