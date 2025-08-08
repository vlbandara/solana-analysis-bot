#!/usr/bin/env python3
"""
Evolution API WhatsApp Client
Integrates with Evolution API for WhatsApp group messaging
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EvolutionWhatsApp:
    """WhatsApp client using Evolution API"""
    
    def __init__(self, base_url: str = "http://localhost:8080", session_name: str = "solana_bot"):
        """Initialize Evolution API client"""
        self.base_url = base_url.rstrip('/')
        self.session_name = session_name
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Optional API key if authentication is enabled
        api_key = os.getenv('EVOLUTION_API_KEY')
        if api_key:
            self.headers['apikey'] = api_key
        
        print(f"🔍 Evolution API initialized: {self.base_url}")
        print(f"📱 Session name: {self.session_name}")
    
    def check_connection(self) -> bool:
        """Check if Evolution API is running"""
        try:
            response = requests.get(f"{self.base_url}/manager/instance/fetchInstances", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                print("✅ Evolution API is running")
                return True
            else:
                print(f"❌ Evolution API responded with status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to Evolution API: {e}")
            return False
    
    def create_session(self) -> bool:
        """Create a new WhatsApp session"""
        try:
            payload = {
                "instanceName": self.session_name,
                "integration": "WHATSAPP-BAILEYS",
                "qrcode": True,
                "webhook_wa_business": {
                    "url": "",
                    "enabled": False
                }
            }
            
            response = requests.post(f"{self.base_url}/manager/instance/create", 
                                   json=payload, headers=self.headers, timeout=30)
            
            if response.status_code in [200, 201]:
                print("✅ Session created successfully")
                return True
            else:
                print(f"❌ Failed to create session: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating session: {e}")
            return False
    
    def get_qr_code(self) -> Optional[str]:
        """Get QR code for WhatsApp authentication"""
        try:
            response = requests.get(f"{self.base_url}/{self.session_name}/instance/qrcode", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'qrcode' in data:
                    print("📱 QR Code received - scan with WhatsApp")
                    return data['qrcode']
                else:
                    print("⚠️ No QR code in response - session might be connected")
                    return None
            else:
                print(f"❌ Failed to get QR code: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting QR code: {e}")
            return None
    
    def check_session_status(self) -> str:
        """Check WhatsApp session connection status"""
        try:
            response = requests.get(f"{self.base_url}/{self.session_name}/instance/connectionState", 
                                  headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                state = data.get('instance', {}).get('state', 'unknown')
                print(f"📱 Session status: {state}")
                return state
            else:
                print(f"❌ Failed to check session status: {response.status_code}")
                return "error"
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking session status: {e}")
            return "error"
    
    def wait_for_connection(self, max_wait_time: int = 60) -> bool:
        """Wait for WhatsApp session to be connected"""
        print("⏳ Waiting for WhatsApp connection...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.check_session_status()
            if status == "open":
                print("✅ WhatsApp connected successfully!")
                return True
            elif status in ["close", "error"]:
                print("❌ WhatsApp connection failed")
                return False
            
            time.sleep(5)
        
        print("⏰ Connection timeout - please try again")
        return False
    
    def get_groups(self) -> List[Dict[str, Any]]:
        """Get list of WhatsApp groups"""
        try:
            response = requests.get(f"{self.base_url}/{self.session_name}/chat/whatsappGroups", 
                                  headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                groups = response.json()
                print(f"📱 Found {len(groups)} WhatsApp groups")
                for group in groups:
                    print(f"  - {group.get('name', 'Unknown')} ({group.get('id', 'No ID')})")
                return groups
            else:
                print(f"❌ Failed to get groups: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting groups: {e}")
            return []
    
    def send_text_message(self, jid: str, message: str) -> bool:
        """Send text message to WhatsApp (individual or group)"""
        try:
            payload = {
                "number": jid,
                "text": message
            }
            
            response = requests.post(f"{self.base_url}/{self.session_name}/message/sendText", 
                                   json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message'):
                    print(f"✅ Message sent successfully to {jid}")
                    return True
                else:
                    print(f"⚠️ Message may not have been sent: {data}")
                    return False
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def send_analysis_to_group(self, group_jid: str, analysis_data: Dict[str, Any]) -> bool:
        """Send Solana analysis to WhatsApp group"""
        try:
            # Create WhatsApp-friendly summary
            summary = self._create_whatsapp_summary(analysis_data)
            
            # Send to group
            return self.send_text_message(group_jid, summary)
            
        except Exception as e:
            print(f"❌ Error sending analysis to group: {e}")
            return False
    
    def _create_whatsapp_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Create a concise WhatsApp-friendly summary"""
        
        # Extract key information
        model_used = analysis_data.get('model_used', 'Unknown')
        timestamp = analysis_data.get('timestamp', '')
        analysis = analysis_data.get('analysis', '')
        
        # Create WhatsApp-friendly summary
        lines = analysis.split('\n')
        summary_lines = []
        
        # Add header
        summary_lines.append("🚀 *SOLANA ANALYSIS UPDATE*")
        summary_lines.append("═" * 30)
        
        # Extract price and key metrics
        price_info = ""
        for line in lines:
            if "Spot reference:" in line or "Current Price:" in line:
                price_parts = line.split("$")
                if len(price_parts) > 1:
                    price_info = price_parts[-1].split()[0]
                    break
        
        if price_info:
            summary_lines.append(f"💰 *SOL Price:* ${price_info}")
        
        # Extract trading recommendation
        recommendation = "NEUTRAL"
        for line in lines:
            if "Direction:" in line or "Directional Bias:" in line:
                if "LONG" in line.upper():
                    recommendation = "🟢 *LONG*"
                elif "SHORT" in line.upper():
                    recommendation = "🔴 *SHORT*"
                break
        
        summary_lines.append(f"📊 *Recommendation:* {recommendation}")
        
        # Extract key levels
        support_level = "N/A"
        resistance_level = "N/A"
        
        for line in lines:
            if "S1" in line and "$" in line:
                parts = line.split("$")
                if len(parts) > 1:
                    support_level = parts[-1].split()[0]
            if "R1" in line and "$" in line:
                parts = line.split("$")
                if len(parts) > 1:
                    resistance_level = parts[-1].split()[0]
        
        summary_lines.append(f"📈 *Resistance:* ${resistance_level}")
        summary_lines.append(f"📉 *Support:* ${support_level}")
        
        # Add model info
        summary_lines.append(f"🤖 *Model:* {model_used}")
        summary_lines.append(f"⏰ *Time:* {datetime.now().strftime('%H:%M UTC')}")
        
        # Add disclaimer
        summary_lines.append("")
        summary_lines.append("⚠️ *Educational purposes only*")
        summary_lines.append("📊 Full analysis available in repo")
        
        return "\n".join(summary_lines)

def send_analysis_to_whatsapp_group(analysis_file: str, group_jid: str) -> bool:
    """Send analysis results to WhatsApp group using Evolution API"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Create Evolution WhatsApp client
        client = EvolutionWhatsApp()
        
        # Check if API is running
        if not client.check_connection():
            print("❌ Evolution API not available")
            return False
        
        # Check session status
        status = client.check_session_status()
        if status != "open":
            print("❌ WhatsApp session not connected")
            return False
        
        # Send analysis to group
        return client.send_analysis_to_group(group_jid, analysis_data)
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending to WhatsApp group: {e}")
        return False

if __name__ == "__main__":
    # Test Evolution API WhatsApp client
    client = EvolutionWhatsApp()
    
    print("🧪 Testing Evolution API WhatsApp client...")
    
    # Check connection
    if client.check_connection():
        print("✅ Evolution API is running")
        
        # Check session status
        status = client.check_session_status()
        print(f"📱 Current session status: {status}")
        
        # If not connected, show QR code
        if status != "open":
            print("📱 Creating session and getting QR code...")
            client.create_session()
            qr_code = client.get_qr_code()
            if qr_code:
                print("📱 Please scan the QR code with WhatsApp")
                print("🔗 QR Code URL:", qr_code)
        
        # Get groups (if connected)
        if status == "open":
            groups = client.get_groups()
            
            if groups:
                print("\n🧪 Testing message send to first group...")
                test_message = f"🧪 Test message from Solana Analysis Bot\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                success = client.send_text_message(groups[0]['id'], test_message)
                
                if success:
                    print("✅ WhatsApp group test successful!")
                else:
                    print("❌ WhatsApp group test failed!")
            else:
                print("⚠️ No groups found - make sure you're in at least one WhatsApp group")
    else:
        print("❌ Evolution API not available - please start the Docker container")