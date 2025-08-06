# GitHub Actions Setup for SOL Analysis

## Overview
This repository includes a GitHub Actions workflow that runs SOL hourly analysis automatically every hour using GitHub's cloud infrastructure.

## Required GitHub Secrets

To enable the automated workflow, you need to add the following secrets to your GitHub repository:

### 1. Go to Repository Settings
- Navigate to your GitHub repository
- Click on **Settings** tab
- Click on **Secrets and variables** → **Actions**
- Click **New repository secret**

### 2. Add Required Secrets

| Secret Name | Description | Example Format |
|-------------|-------------|----------------|
| `COINALYZE_API_KEY` | API key from Coinalyze for market data | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `OPENAI_API_KEY` | OpenAI API key for o3 model analysis | `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID for WhatsApp | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp sender number | `+1234567890` |
| `AUTO_SEND_TO_WHATSAPP` | Your WhatsApp number to receive alerts | `+1234567890` |

### 3. Workflow Schedule
The workflow is configured to run:
- **Automatically**: Every hour at minute 5 (5 minutes past each hour)
- **Manually**: You can trigger it manually from the Actions tab

### 4. Workflow Features
- ✅ **Robust execution**: 10-minute timeout with proper error handling
- ✅ **Enhanced dependencies**: Automatic installation of all required packages
- ✅ **WhatsApp control**: Enable/disable WhatsApp sending via manual trigger
- ✅ **Failure notifications**: Automatic WhatsApp alerts if workflow fails
- ✅ **Artifact archiving**: Analysis results saved for 3 days
- ✅ **Dependency verification**: Pre-run checks ensure all packages installed
- ✅ **Environment isolation**: Clean virtual environment for each run

### 5. Manual Trigger Options
You can manually trigger the workflow with options:
1. Go to **Actions** tab in your repository
2. Click on **SOL Hourly Analysis** workflow
3. Click **Run workflow** button
4. **Choose WhatsApp setting**:
   - `true` - Send WhatsApp messages (default)
   - `false` - Run analysis only, no WhatsApp
5. Click **Run workflow** to confirm

### 6. Automatic Failure Handling
If the workflow fails:
- ✅ **Automatic WhatsApp notification** sent to your number
- ✅ **Error logs** archived as artifacts
- ✅ **Detailed GitHub Actions logs** for debugging

### 7. Monitoring
- Check the **Actions** tab to see workflow runs
- Download artifacts to see analysis results
- View logs for debugging if needed

## Local Development
For local development, copy `.env.example` to `.env` and add your actual API keys.

## Security Notes
- Never commit actual API keys to the repository
- Use GitHub Secrets for all sensitive data
- The `.env` file is gitignored for security