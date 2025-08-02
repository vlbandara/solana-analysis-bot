#!/usr/bin/env python3
"""
WhatsApp Selenium Integration for Solana Analysis
Uses browser automation to send messages to WhatsApp Web
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

class WhatsAppSelenium:
    def __init__(self):
        self.driver = None
        self.group_name = os.getenv('WHATSAPP_GROUP_NAME', 'Solana Analysis')
        
    def setup_driver(self):
        """Setup Chrome driver with WhatsApp Web"""
        try:
            # Setup Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Navigate to WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            
            print("📱 Please scan QR code to login to WhatsApp Web...")
            print("⏳ Waiting for WhatsApp Web to load...")
            
            # Wait for WhatsApp Web to load
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            
            print("✅ WhatsApp Web loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup error: {e}")
            return False
    
    def find_group(self, group_name: str) -> bool:
        """Find and click on the target group"""
        try:
            # Search for the group
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_box.clear()
            search_box.send_keys(group_name)
            time.sleep(2)
            
            # Click on the group
            group_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//span[contains(text(), "{group_name}")]'))
            )
            group_element.click()
            time.sleep(1)
            
            print(f"✅ Found group: {group_name}")
            return True
            
        except Exception as e:
            print(f"❌ Group not found: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send message to the current group"""
        try:
            # Find message input box
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="6"]'))
            )
            
            # Clear and type message
            message_box.clear()
            message_box.send_keys(message)
            time.sleep(1)
            
            # Send message
            message_box.send_keys(Keys.ENTER)
            time.sleep(2)
            
            print("✅ Message sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Send message error: {e}")
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

def send_analysis_via_selenium(analysis_file: str = 'o3_enhanced_analysis.json'):
    """Send analysis using Selenium WhatsApp Web"""
    whatsapp = WhatsAppSelenium()
    
    try:
        # Setup driver
        if not whatsapp.setup_driver():
            return False
        
        # Load analysis
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Format message
        message = whatsapp.format_analysis_for_whatsapp(analysis_data)
        
        # Find group
        if not whatsapp.find_group(whatsapp.group_name):
            print(f"❌ Group '{whatsapp.group_name}' not found")
            return False
        
        # Send message
        success = whatsapp.send_message(message)
        
        if success:
            print("🎯 Analysis sent to WhatsApp group via Selenium!")
        
        return success
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return False
    finally:
        whatsapp.close()

if __name__ == "__main__":
    send_analysis_via_selenium() 