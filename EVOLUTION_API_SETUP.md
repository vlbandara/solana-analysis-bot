# 🚀 Evolution API WhatsApp Integration Setup

This guide will help you set up Evolution API locally to send your Solana analysis to WhatsApp groups instead of using Twilio.

## 🎯 Why Evolution API?

- ✅ **Free WhatsApp messaging** (no Twilio costs)
- ✅ **Direct group messaging** (no individual number limits)
- ✅ **Rich formatting** (bold, italic, emojis)
- ✅ **No template restrictions** (send any message)
- ✅ **Multiple groups support**

## 📋 Prerequisites

1. **Docker Desktop** installed and running
2. **Python 3.8+** with pip or uv
3. **WhatsApp account** (for QR code scanning)
4. **WhatsApp groups** you want to send messages to

## 🚀 Quick Start

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your Mac.

### Step 2: Run the Setup Script
```bash
./start_evolution_test.sh
```

This script will:
- Start Evolution API container
- Install Python dependencies
- Run the setup process
- Guide you through WhatsApp QR code scanning

### Step 3: Scan QR Code
When prompted, scan the QR code with WhatsApp:
1. Open WhatsApp on your phone
2. Go to Settings → Linked Devices
3. Tap "Link a Device"
4. Scan the QR code shown in terminal

### Step 4: Test the Integration
The script will automatically test sending a message to your first WhatsApp group.

## 📱 Manual Setup (if script fails)

### 1. Start Evolution API
```bash
docker-compose -f docker-compose.evolution.yml up -d
```

### 2. Install Dependencies
```bash
# Using uv (recommended)
uv add requests qrcode[pil]

# Or using pip
pip install requests qrcode[pil]
```

### 3. Run Setup
```bash
python3 setup_evolution.py
```

### 4. Test Integration
```bash
python3 evolution_whatsapp.py
```

## 🔧 Configuration

### Environment Variables (Optional)
Create a `.env` file with:
```env
# Evolution API Configuration (optional)
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your_api_key_if_auth_enabled
EVOLUTION_SESSION_NAME=solana_bot
```

### Group Configuration
After setup, your group information is saved in `whatsapp_groups.json`:
```json
{
  "groups": [...],
  "primary_group_jid": "120363025565841915@g.us",
  "primary_group_name": "Solana Trading Signals",
  "setup_time": "2025-01-27 15:30:45"
}
```

## 🔄 Integration with Existing Workflow

### Option 1: Use Enhanced Sender (Recommended)
Replace your existing WhatsApp calls with:
```python
from enhanced_whatsapp_sender import send_analysis_to_whatsapp

# This will try Evolution API first, fallback to Twilio
success = send_analysis_to_whatsapp('sol_analysis_state.json', prefer_evolution=True)
```

### Option 2: Update Existing Scripts
Modify your current scripts to import the enhanced sender:
```python
# Replace this line:
# from whatsapp_sender import send_analysis_to_whatsapp

# With this:
from enhanced_whatsapp_sender import send_analysis_to_whatsapp
```

### Option 3: Direct Evolution API Usage
For full control:
```python
from evolution_whatsapp import EvolutionWhatsApp

client = EvolutionWhatsApp()
client.send_text_message("120363025565841915@g.us", "Your message")
```

## 📊 Testing

### Test Basic Connection
```bash
python3 evolution_whatsapp.py
```

### Test Enhanced Sender
```bash
python3 enhanced_whatsapp_sender.py
```

### Test with Real Analysis
```bash
# Run your existing analysis
python3 sol_hourly_analysis.py

# The enhanced sender will automatically use Evolution API
```

## 🛠️ Troubleshooting

### Evolution API Not Starting
```bash
# Check Docker containers
docker ps

# View Evolution API logs
docker-compose -f docker-compose.evolution.yml logs -f evolution-api

# Restart container
docker-compose -f docker-compose.evolution.yml restart evolution-api
```

### WhatsApp Connection Issues
```bash
# Check session status
curl http://localhost:8080/solana_bot/instance/connectionState

# Get new QR code
curl http://localhost:8080/solana_bot/instance/qrcode
```

### Group Not Found
1. Make sure you're a member of the WhatsApp group
2. Re-run setup to refresh group list:
   ```bash
   python3 setup_evolution.py
   ```

### Port Already in Use
If port 8080 is busy, edit `docker-compose.evolution.yml`:
```yaml
ports:
  - "8081:8080"  # Use port 8081 instead
```

Then update the Evolution API URL:
```python
client = EvolutionWhatsApp(base_url="http://localhost:8081")
```

## 🔄 Production Deployment

### For GitHub Actions
Add these secrets:
- `EVOLUTION_API_URL`: Your Evolution API server URL
- `EVOLUTION_API_KEY`: API key (if authentication enabled)
- `WHATSAPP_GROUP_JID`: Target group ID

### For VPS/Server
1. Use proper domain and SSL:
   ```yaml
   environment:
     - SERVER_URL=https://your-domain.com
   ```

2. Enable authentication:
   ```yaml
   environment:
     - AUTHENTICATION_TYPE=jwt
     - AUTHENTICATION_JWT_EXPIRIN_IN=0
     - AUTHENTICATION_JWT_SECRET=your_secret_key
   ```

## 📋 API Endpoints Reference

### Instance Management
- `POST /manager/instance/create` - Create session
- `GET /manager/instance/fetchInstances` - List instances
- `GET /{session}/instance/connectionState` - Check connection
- `GET /{session}/instance/qrcode` - Get QR code

### Messaging
- `POST /{session}/message/sendText` - Send text message
- `POST /{session}/message/sendMedia` - Send media
- `GET /{session}/chat/whatsappGroups` - List groups

### Full API Documentation
Visit: http://localhost:8080/docs (when Evolution API is running)

## 🎉 Success Indicators

✅ **Setup Successful When You See:**
- "Evolution API is ready!"
- "WhatsApp connected successfully!"
- "Test message sent successfully!"
- Message appears in your WhatsApp group

✅ **Integration Working When:**
- Your hourly analysis appears in WhatsApp group
- Messages have rich formatting (bold, emojis)
- No Twilio costs incurred
- Multiple groups can receive messages

## 🆘 Support

If you encounter issues:

1. **Check the logs:**
   ```bash
   docker-compose -f docker-compose.evolution.yml logs -f evolution-api
   ```

2. **Verify Evolution API is running:**
   ```bash
   curl http://localhost:8080/manager/instance/fetchInstances
   ```

3. **Test Python integration:**
   ```bash
   python3 -c "from evolution_whatsapp import EvolutionWhatsApp; print('✅ Import successful')"
   ```

4. **Check group configuration:**
   ```bash
   cat whatsapp_groups.json
   ```

## 🔗 Useful Links

- [Evolution API GitHub](https://github.com/EvolutionAPI/evolution-api)
- [Evolution API Documentation](https://doc.evolution-api.com/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)

---

**Ready to test?** Start Docker Desktop and run: `./start_evolution_test.sh` 🚀