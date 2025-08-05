# WhatsApp Template Setup - QUICK SOLUTION for Error 63016

## 🎯 IMMEDIATE FIX: Simple Template Approach

**Error 63016**: "Failed to send freeform message because you are outside the allowed window"

**Solution**: Create a simple approved WhatsApp template (gets approved in minutes!)

### ⚡ Quick Template (Recommended)

Create this **simple template** in your **Twilio Console → Content Manager**:

#### Template Name: `trading_update`

#### Template Content:
```
Your trading update: {{1}}
```

#### Variable Mapping:
- `{{1}}` = Complete SOL derivatives analysis message (our entire formatted message)

### 🛠️ Setup Steps (5 minutes):

#### 1. Create Simple Template in Twilio Console
1. Go to **Twilio Console → Content Manager**
2. Click **Create Template**
3. Fill out the form:
   - **Template Name**: `trading_update`
   - **Category**: `UTILITY` (for financial/trading information)
   - **Language**: `English`
   - **Message Body**: `Your trading update: {{1}}`
4. Click **Submit for Approval**
5. ⚡ **Usually approved within 5-15 minutes** (simple templates are fast!)

#### 2. Get Template Content SID
After approval (check status in Content Manager):
1. Click on your approved template
2. Copy the **Content SID** (starts with `HX...`)

#### 3. Set GitHub Secrets
Add this secret to your repository settings:

```bash
TWILIO_WHATSAPP_TEMPLATE_SID=HXxxxxxxxxxxxxxxxxxxxxx
```

**Remove this if set:**
```bash
TWILIO_USE_TEMPLATE=false  # Remove this line or set to true
```

### 🔄 Fallback Mode

If no template is configured, the system will:
1. Try to send as regular WhatsApp message
2. Work within 24-hour session window
3. Show helpful error messages if template is needed

### 🧪 Testing Your Template

Test your template setup:
```bash
# Run WhatsApp template test
python enhanced_solana_workflow.py --test-whatsapp
```

### ✅ Why This Simple Template Works

✅ **Fast Approval**: Simple templates approved in 5-15 minutes  
✅ **Reliable Delivery**: Works 24/7 outside session windows  
✅ **No Variable Limits**: Single variable can contain entire message  
✅ **UTILITY Category**: Perfect for financial/trading alerts  
✅ **Compliance**: Meets WhatsApp Business API requirements  

### 🎯 Template Approval Tips

**✅ DO:**
- Keep templates simple and clear
- Use "UTILITY" category for trading/financial updates
- Include context like "Your trading update"
- Submit during business hours for faster review

**❌ DON'T:**
- Use complex multi-variable templates (slower approval)
- Put variables at the start or end of messages
- Use gambling/promotional language
- Submit duplicate templates

### ⚠️ Error 63016 Troubleshooting

If you still get error 63016:
1. ✅ **Template approved?** Check Content Manager status
2. ✅ **Correct Content SID?** Must start with `HX...`
3. ✅ **GitHub Secret set?** `TWILIO_WHATSAPP_TEMPLATE_SID`
4. ✅ **Template active?** Not paused or disabled

---

**Need Help?** Check Twilio's [WhatsApp Template Documentation](https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-messages-templates)