# WhatsApp Template Setup for SOL Derivatives Agent

## 📋 Required: Create WhatsApp Message Template

For the SOL Derivatives Analysis Agent to work with WhatsApp Business API, you need an **approved message template**.

### 🎯 Template Structure

Create this template in your **Twilio Console → Messaging → Content Manager**:

#### Template Name: `sol_derivatives_alert`

#### Template Content:
```
{{1}}
```

#### Variable Mapping:
- `{{1}}` = Complete SOL derivatives analysis message

This simple template passes the entire formatted analysis as a single variable, making it more reliable and easier to manage.

### 🛠️ Setup Steps:

#### 1. Create Template in Twilio Console
1. Go to **Twilio Console → Messaging → Content Template Builder**
2. Click **Create new Template**
3. Fill out the form:
   - **Template name**: `sol_derivatives_alert`
   - **Template category**: `UTILITY` (for market/trading information)
   - **Message language**: `English`
   - **Message body**: `{{1}}` (just this single placeholder)
4. Add sample content for the variable:
   - Variable 1 sample: `SOL Analysis: Price $166.14, OI $1.5B, Funding -0.36%`
5. Click **Save and submit for WhatsApp approval**

#### 2. Wait for Approval
- Approval usually takes 5 minutes to 24 hours
- Check status in Content Template Builder
- You'll see status: Pending → Approved

#### 3. Get Template SID
After approval:
1. Go to **Content Template Builder**
2. Find your `sol_derivatives_alert` template
3. Click on it to view details
4. Copy the **Content SID** (starts with `HX...`)

#### 4. Set GitHub Secrets
Add these secrets to your repository settings:

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

### 🆘 Troubleshooting Error 63016

**Error**: `63016 - Failed to send freeform message because you are outside the allowed window. If you are using WhatsApp, please use a Message Template.`

**Solution**:
1. ✅ **Create approved template** (steps above)
2. ✅ **Set template SID** in GitHub Secrets
3. ✅ **Enable template mode**: `TWILIO_USE_TEMPLATE=true`

**Why this happens**:
- WhatsApp Business API requires approved templates for outbound messages
- 24-hour session window has expired 
- Automated hourly alerts always need templates

**Quick Test**:
```bash
# Test template in your environment
python enhanced_solana_workflow.py --test-whatsapp
```

---

**Need Help?** Check Twilio's [WhatsApp Template Documentation](https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-messages-templates)