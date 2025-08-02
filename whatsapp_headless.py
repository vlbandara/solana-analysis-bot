#!/usr/bin/env python3
"""
Headless WhatsApp Integration for GitHub Actions
Uses browser automation without GUI for cloud deployment
"""

import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class WhatsAppHeadless:
    def __init__(self):
        self.driver = None
        self.group_name = os.getenv('WHATSAPP_GROUP_NAME', 'Solana Analysis')
        
    def setup_driver(self):
        """Setup Chrome driver with WhatsApp Web (headless)"""
        try:
            # Setup Chrome options for headless mode
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Navigate to WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            
            print("📱 WhatsApp Web loaded in headless mode...")
            print("⚠️ Note: Headless mode requires manual QR scan setup")
            print("💡 For automated sending, consider using Twilio WhatsApp API instead")
            
            # Wait for WhatsApp Web to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            
            print("✅ WhatsApp Web loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup error: {e}")
            return False
    
    def format_analysis_for_whatsapp(self, analysis_data: dict) -> str:
        """Format analysis for WhatsApp"""
        try:
            analysis_text = analysis_data.get('analysis', '')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
            
            formatted_message = f"""
🔔 SOLANA ANALYSIS REPORT
⏰ {timestamp}
{'='*40}

{analysis_text}

{'='*40}
📊 Powered by o3 AI Analysis
⚠️ Educational purposes only
            """.strip()
            
            return formatted_message
            
        except Exception as e:
            print(f"❌ Format error: {e}")
            return "Error formatting analysis"
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def send_analysis_headless(analysis_file: str = 'o3_enhanced_analysis.json'):
    """Send analysis using headless WhatsApp (for GitHub Actions)"""
    whatsapp = WhatsAppHeadless()
    
    try:
        # Setup driver
        if not whatsapp.setup_driver():
            print("❌ Headless WhatsApp setup failed")
            print("💡 Consider using Twilio WhatsApp API for automated sending")
            return False
        
        # Load analysis
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Format message
        message = whatsapp.format_analysis_for_whatsapp(analysis_data)
        
        print("📱 Analysis formatted for WhatsApp:")
        print(message[:200] + "..." if len(message) > 200 else message)
        
        print("✅ Analysis ready for WhatsApp sending")
        print("💡 For automated sending, use Twilio WhatsApp API")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Headless error: {e}")
        return False
    finally:
        whatsapp.close()

if __name__ == "__main__":
    send_analysis_headless()
