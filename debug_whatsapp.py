#!/usr/bin/env python3

# Add debugging to whatsapp_sender.py
with open('whatsapp_sender.py', 'r') as f:
    content = f.read()

# Add debug prints to the __init__ method
debug_init = '''
    def __init__(self):
        """Initialize WhatsApp sender with Twilio credentials"""
        print("🔍 DEBUG: Initializing WhatsApp sender...")
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM')
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        print(f"🔍 DEBUG: Account SID: {'✅ Set' if self.account_sid else '❌ Missing'}")
        print(f"🔍 DEBUG: Auth Token: {'✅ Set' if self.auth_token else '❌ Missing'}")
        print(f"🔍 DEBUG: From Number: {'✅ Set' if self.from_number else '❌ Missing'}")
        print(f"🔍 DEBUG: To Number: {'✅ Set' if self.to_number else '❌ Missing'}")
        
        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):
            print("⚠️ Missing Twilio credentials in .env file")
            self.client = None
        elif TWILIO_AVAILABLE:
            print("🔍 DEBUG: Creating Twilio client...")
            self.client = Client(self.account_sid, self.auth_token)
            print("✅ DEBUG: Twilio client created successfully")
        else:
            print("❌ DEBUG: Twilio library not available")
            self.client = None
'''

# Replace the __init__ method
content = content.replace(
    '    def __init__(self):\n        """Initialize WhatsApp sender with Twilio credentials"""\n        self.account_sid = os.getenv(\'TWILIO_ACCOUNT_SID\')\n        self.auth_token = os.getenv(\'TWILIO_AUTH_TOKEN\')\n        self.from_number = os.getenv(\'TWILIO_WHATSAPP_FROM\')\n        self.to_number = os.getenv(\'WHATSAPP_TO_NUMBER\')\n        \n        if not all([self.account_sid, self.auth_token, self.from_number, self.to_number]):\n            print("⚠️ Missing Twilio credentials in .env file")\n            self.client = None\n        elif TWILIO_AVAILABLE:\n            self.client = Client(self.account_sid, self.auth_token)\n        else:\n            self.client = None',
    debug_init
)

# Add debug to send_message method
debug_send = '''
    def send_message(self, message: str) -> bool:
        """Send message to WhatsApp"""
        print("🔍 DEBUG: Attempting to send WhatsApp message...")
        if not self.client:
            print("❌ Twilio client not available")
            return False
        
        try:
            print(f"🔍 DEBUG: Sending to: whatsapp:{self.to_number}")
            print(f"🔍 DEBUG: From: whatsapp:{self.from_number}")
            message = self.client.messages.create(
                from_=f'whatsapp:{self.from_number}',
                body=message,
                to=f'whatsapp:{self.to_number}'
            )
            print(f"✅ WhatsApp message sent: {message.sid}")
            return True
        except TwilioException as e:
            print(f"❌ Twilio error: {e}")
            return False
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            return False
'''

# Replace the send_message method
content = content.replace(
    '    def send_message(self, message: str) -> bool:\n        """Send message to WhatsApp"""\n        if not self.client:\n            print("❌ Twilio client not available")\n            return False\n        \n        try:\n            message = self.client.messages.create(\n                from_=f\'whatsapp:{self.from_number}\',\n                body=message,\n                to=f\'whatsapp:{self.to_number}\'\n            )\n            print(f"✅ WhatsApp message sent: {message.sid}")\n            return True\n        except TwilioException as e:\n            print(f"❌ Twilio error: {e}")\n            return False\n        except Exception as e:\n            print(f"❌ WhatsApp send error: {e}")\n            return False',
    debug_send
)

# Write back
with open('whatsapp_sender.py', 'w') as f:
    f.write(content)

print("Added debugging to whatsapp_sender.py")
