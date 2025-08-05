# WhatsApp Template Setup for SOL Derivatives Agent

## 📋 Required: Create WhatsApp Message Template

For the SOL Derivatives Analysis Agent to work with WhatsApp Business API, you need an **approved message template**.

### 🎯 Template Structure

Create this template in your **Twilio Console → Messaging → Content Manager**:

#### Template Name: `sol_derivatives_alert`

#### Template Content:
```
🎯 SOL DERIVATIVES ALERT • {{1}}

📊 ${{2}} | OI: {{3}}
💸 Funding: {{4}} | Bias: {{5}}

{{6}}

📈 Coinalyze + o3
```

#### Variable Mapping:
- `{{1}}` = Timestamp (e.g., "08:30 UTC")
- `{{2}}` = SOL Price (e.g., "166.14")
- `{{3}}` = Open Interest (e.g., "$1.51B (-$10M 24h)")
- `{{4}}` = Funding Rate (e.g., "-0.36%")
- `{{5}}` = Market Bias (e.g., "LONG")
- `{{6}}` = Analysis content (Key insights, risks, actions)

### 🛠️ Setup Steps:

#### 1. Create Template in Twilio Console
1. Go to **Twilio Console → Messaging → Content Manager**
2. Click **Create new Template**
3. Choose **WhatsApp** as channel
4. Use the template content above
5. Submit for approval (usually takes 24-48 hours)

#### 2. Get Template SID
After approval, copy the Template SID (looks like `HX...`)

#### 3. Set GitHub Secrets
Add these secrets to your repository:

```bash
TWILIO_WHATSAPP_TEMPLATE_SID=HXxxxxxxxxxxxxxxxxxxxxx
TWILIO_USE_TEMPLATE=true
```

### 🔄 Fallback Mode

If no template is configured, the system will:
1. Try to send as regular WhatsApp message
2. Work within 24-hour session window
3. Show helpful error messages if template is needed

### 🧪 Testing

Test your template setup:
```bash
# Run WhatsApp template test
python enhanced_solana_workflow.py --test-whatsapp
```

### 📱 Template Benefits

✅ **Reliable Delivery**: Works outside 24-hour session window  
✅ **Professional Format**: Consistent, approved messaging  
✅ **Lower Costs**: Template messages often have lower rates  
✅ **Compliance**: Meets WhatsApp Business API requirements  

### ⚠️ Important Notes

1. **Approval Required**: Templates must be approved by WhatsApp
2. **No Emojis in Variables**: Keep variables text-only
3. **Content Limits**: Each variable has character limits
4. **Template Changes**: Require re-approval if modified

### 💡 Alternative: Sandbox Mode

For testing only, you can:
1. Use Twilio WhatsApp Sandbox
2. Set `TWILIO_USE_TEMPLATE=false`
3. Ensure recipient has messaged the sandbox within 24 hours

---

**Need Help?** Check Twilio's [WhatsApp Template Documentation](https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-messages-templates)