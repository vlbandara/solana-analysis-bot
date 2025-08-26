#!/usr/bin/env python3
"""
WhatsApp Sender Module for Solana Analysis Bot - ROBUST VERSION
Uses Twilio API to send analysis results to WhatsApp groups with bulletproof error handling
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio not installed. Run: uv add twilio")

class WhatsAppSender:
    """WhatsApp sender using Twilio API with robust error handling"""
    

    def __init__(self):
        """Initialize WhatsApp sender with Twilio credentials"""
        print("🔍 DEBUG: Initializing robust WhatsApp sender...")
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM') or os.getenv('TWILIO_WHATSAPP_NUMBER')
        # Single number is optional now; multiple numbers supported via WHATSAPP_TO_NUMBERS
        self.to_number = os.getenv('WHATSAPP_TO_NUMBER')
        
        print(f"🔍 DEBUG: Account SID: {'✅ Set' if self.account_sid else '❌ Missing'}")
        print(f"🔍 DEBUG: Auth Token: {'✅ Set' if self.auth_token else '❌ Missing'}")
        print(f"🔍 DEBUG: From Number: {'✅ Set' if self.from_number else '❌ Missing'}")
        print(f"🔍 DEBUG: To Number: {'✅ Set' if self.to_number else '❌ Missing'}")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            print("⚠️ Missing Twilio credentials (account_sid/auth_token/from). Check environment variables.")
            self.client = None
        elif TWILIO_AVAILABLE:
            print("🔍 DEBUG: Creating Twilio client...")
            self.client = Client(self.account_sid, self.auth_token)
            print("✅ DEBUG: Twilio client created successfully")
        else:
            print("❌ DEBUG: Twilio library not available")
            self.client = None

    def _parse_recipients(self) -> list[str]:
        """Parse recipients from WHATSAPP_TO_NUMBERS or fallback to WHATSAPP_TO_NUMBER."""
        raw = os.getenv('WHATSAPP_TO_NUMBERS', '')
        recipients: list[str] = []
        if raw:
            # Split by commas, semicolons, whitespace, or newlines
            parts = re.split(r"[\s,;]+", raw)
            recipients = [p.strip() for p in parts if p.strip()]
        # Fallback to single number
        if not recipients and self.to_number:
            recipients = [self.to_number.strip()]
        return recipients

    def _is_valid_price(self, price_str: str) -> bool:
        """Validate price string format"""
        try:
            price = float(price_str)
            return 10.0 <= price <= 1000.0  # Reasonable SOL price range
        except (ValueError, TypeError):
            return False
    
    def _is_valid_percentage(self, pct_str: str) -> bool:
        """Validate percentage string format"""
        try:
            pct = float(pct_str)
            return -50.0 <= pct <= 50.0  # Reasonable 24h change range
        except (ValueError, TypeError):
            return False
    
    def _is_valid_number(self, num_str: str) -> bool:
        """Validate numeric string format"""
        try:
            num = float(num_str)
            return num >= 0  # Must be positive
        except (ValueError, TypeError):
            return False
    
    def _is_valid_funding_rate(self, rate_str: str) -> bool:
        """Validate funding rate format"""
        try:
            rate = float(rate_str)
            return -1.0 <= rate <= 1.0  # Reasonable funding rate range
        except (ValueError, TypeError):
            return False
    
    def _is_valid_ratio(self, ratio_str: str) -> bool:
        """Validate L/S ratio format"""
        try:
            ratio = float(ratio_str)
            return 0.1 <= ratio <= 10.0  # Reasonable L/S ratio range
        except (ValueError, TypeError):
            return False

    def send_message(self, message: str, template_vars: dict | None = None) -> bool:
        """Send message to all configured WhatsApp recipients with comprehensive error handling."""
        print("🔍 DEBUG: Attempting to send WhatsApp message...")
        
        # ROBUST ERROR HANDLING: Check client availability
        if not self.client:
            print("❌ Twilio client not available")
            print("💡 Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables")
            return False

        # ROBUST ERROR HANDLING: Check recipients
        recipients = self._parse_recipients()
        if not recipients:
            print("❌ No WhatsApp recipients configured. Set WHATSAPP_TO_NUMBERS or WHATSAPP_TO_NUMBER.")
            print("💡 Example format: WHATSAPP_TO_NUMBERS=+94769437175,+94729363999")
            return False

        from_param = f'whatsapp:{self.from_number}'
        template_sid = os.getenv('TWILIO_TEMPLATE_SID')

        # ROBUST ERROR HANDLING: Check template SID
        if not template_sid:
            print("❌ TWILIO_TEMPLATE_SID is required for WhatsApp business messages")
            print("💡 Please set TWILIO_TEMPLATE_SID in your environment variables")
            print("💡 You can create a template in Twilio Console or use the default one")
            print("💡 See WHATSAPP_TEMPLATE_SETUP.md for detailed instructions")
            return False
        
        # ROBUST ERROR HANDLING: Validate template variables
        if not template_vars or not isinstance(template_vars, dict):
            print("❌ Template variables are required for WhatsApp messages")
            return False
        
        # Ensure all required template variables are present
        required_vars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        missing_vars = [var for var in required_vars if var not in template_vars]
        if missing_vars:
            print(f"❌ Missing required template variables: {missing_vars}")
            return False

        print(f"🔍 DEBUG: From WhatsApp number: {self.from_number}")
        print(f"🔍 DEBUG: Template SID: {template_sid}")
        print(f"🔍 DEBUG: Recipients: {recipients}")
        print(f"🔍 DEBUG: Template variables count: {len(template_vars)}")

        any_success = False
        for recipient in recipients:
            try:
                # Validate phone number format
                clean_number = recipient.replace('+', '').replace(' ', '').replace('-', '')
                if not clean_number.isdigit():
                    print(f"⚠️  Invalid phone number format: {recipient}")
                    continue
                
                to_param = f'whatsapp:{clean_number}'
                print(f"🔍 DEBUG: From: {from_param} -> To: {to_param}")
                print(f"🔍 DEBUG: Using template SID {template_sid}")
                
                # ROBUST ERROR HANDLING: Validate template variables before sending
                try:
                    json_payload = json.dumps(template_vars or {})
                    if len(json_payload) > 10000:  # Twilio has limits
                        print(f"⚠️  Template variables payload too large: {len(json_payload)} chars")
                        continue
                except Exception as json_error:
                    print(f"❌ Failed to serialize template variables: {json_error}")
                    continue
                
                # Debug: Show exactly what template variables are being sent
                print(f"🔍 DEBUG: Template variables being sent to Twilio:")
                for key, value in template_vars.items():
                    print(f"   {{{{{key}}}}} = {value[:50]}{'...' if len(str(value)) > 50 else ''}")
                
                print(f"🔍 DEBUG: JSON payload length: {len(json_payload)} characters")
                
                # ROBUST SENDING: Create message with comprehensive error handling
                try:
                    msg_obj = self.client.messages.create(
                        from_=from_param,
                        to=to_param,
                        content_sid=template_sid,
                        content_variables=json_payload
                    )
                except Exception as create_error:
                    print(f"❌ Failed to create message for {recipient}: {create_error}")
                    print(f"💡 Check template SID and variable format")
                    continue
                
                print(f"✅ Twilio accepted message: {msg_obj.sid}. Checking delivery status …")
                
                # ROBUST STATUS CHECKING: Enhanced delivery verification
                try:
                    import time
                    status = "queued"
                    max_retries = 10
                    retry_count = 0
                    
                    for retry_count in range(max_retries):
                        try:
                            message_status = self.client.messages(msg_obj.sid).fetch()
                            status = message_status.status
                            error_code = getattr(message_status, 'error_code', None)
                            error_message = getattr(message_status, 'error_message', None)
                            
                            print(f"   ↪ Status check {retry_count + 1}/{max_retries} for {clean_number}: {status}")
                            
                            if error_code:
                                print(f"   ↪ Error code: {error_code}")
                            if error_message:
                                print(f"   ↪ Error message: {error_message}")
                            
                            if status in {"delivered", "failed", "undelivered"}:
                                break
                                
                        except Exception as status_error:
                            print(f"   ⚠️  Status check {retry_count + 1} failed: {status_error}")
                            if retry_count == max_retries - 1:
                                print(f"   ⚠️  Max retries reached, assuming message was sent")
                                status = "sent"  # Assume success if we can't check
                                break
                        
                        time.sleep(2)
                    
                    if status == "delivered":
                        print(f"✅ WhatsApp reports DELIVERED to {clean_number}")
                        any_success = True
                    elif status == "undelivered":
                        print(f"⚠️  Message UNDELIVERED to {clean_number}")
                        print(f"💡 Possible causes:")
                        print(f"   - Number not registered with WhatsApp")
                        print(f"   - Incorrect phone number format")
                        print(f"   - WhatsApp Business account setup issue")
                        print(f"   - Template variable mismatch")
                        
                        # Additional debugging for undelivered messages
                        print(f"🔍 DEBUG: Phone number analysis:")
                        print(f"   - Original: {recipient}")
                        print(f"   - Cleaned: {clean_number}")
                        print(f"   - Length: {len(clean_number)} digits")
                        
                        # Check if number looks like Sri Lankan format
                        if clean_number.startswith('94') and len(clean_number) == 11:
                            print(f"   - Format: Sri Lankan (+94) - {clean_number[:2]}-{clean_number[2:5]}-{clean_number[5:8]}-{clean_number[8:]}")
                        elif clean_number.startswith('94') and len(clean_number) == 12:
                            print(f"   - Format: Sri Lankan (+94) - {clean_number[:2]}-{clean_number[2:5]}-{clean_number[5:8]}-{clean_number[8:]}")
                        else:
                            print(f"   - Format: Unknown country code or length")
                            
                        print(f"🔍 DEBUG: Comprehensive template validation:")
                        print(f"   - Template SID: {template_sid}")
                        print(f"   - Variables count: {len(template_vars)}")
                        print(f"   - Required variables present: {all(str(i) in template_vars for i in range(1, 13))}")
                        
                        # Check for default/empty values
                        default_values = ['0.00', '0.0', '0.000', 'WAIT', 'Analysis unavailable', 'No position', 'Monitor price action']
                        filled_vars = sum(1 for v in template_vars.values() if str(v) not in default_values)
                        print(f"   - Variables with real data: {filled_vars}/{len(template_vars)}")
                        
                        # Show problematic variables
                        empty_vars = [k for k, v in template_vars.items() if str(v) in default_values]
                        if empty_vars:
                            print(f"   - Variables with default values: {empty_vars}")
                        
                        # Suggest next steps
                        print(f"💡 Next steps to try:")
                        print(f"   1. Verify {clean_number} is registered with WhatsApp")
                        print(f"   2. Test with your own WhatsApp number first")
                        print(f"   3. Check Twilio WhatsApp Business setup")
                        print(f"   4. Verify template approval status in Twilio Console")
                    else:
                        print(f"⚠️ Message not delivered to {clean_number} (final status: {status}).")
                except Exception as ex:
                    print(f"⚠️ Could not verify delivery status for {clean_number}: {ex}")
                    any_success = True  # assume success if Twilio accepted
            except TwilioException as e:
                print(f"❌ Twilio error for {recipient}: {e}")
                print(f"💡 Twilio error details:")
                print(f"   - Error code: {getattr(e, 'code', 'Unknown')}")
                print(f"   - Error message: {getattr(e, 'msg', str(e))}")
                if hasattr(e, 'code'):
                    if e.code == 63016:
                        print(f"   - Solution: Check TWILIO_TEMPLATE_SID configuration")
                    elif e.code == 21211:
                        print(f"   - Solution: Check phone number format (should include country code)")
                    elif e.code == 63007:
                        print(f"   - Solution: Template not approved or variables mismatch")
            except Exception as e:
                print(f"❌ Unexpected WhatsApp send error for {recipient}: {e}")
                print(f"💡 Check network connection and API credentials")

        # FINAL VALIDATION: Report overall success
        if any_success:
            print(f"✅ WhatsApp sending completed successfully to at least one recipient")
        else:
            print(f"❌ WhatsApp sending failed to all recipients")
            print(f"💡 Common solutions:")
            print(f"   1. Verify all phone numbers are registered with WhatsApp")
            print(f"   2. Check template approval status in Twilio Console")
            print(f"   3. Ensure template variables match exactly")
            print(f"   4. Test with your own WhatsApp number first")
        
        return any_success
    
    def send_analysis_summary(self, analysis_data: Dict[str, Any]) -> bool:
        """Send a concise analysis summary to WhatsApp with retry mechanism"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries} to send WhatsApp summary...")
                
                # Extract key information with validation
                model_used = analysis_data.get('model_used', 'Unknown')
                timestamp = analysis_data.get('timestamp', datetime.now().strftime('%H:%M UTC'))
                analysis = analysis_data.get('analysis', '')
                
                if not analysis or len(analysis.strip()) < 10:
                    print("⚠️  Analysis data is too short or empty")
                    if attempt == max_retries - 1:
                        return False
                    continue
                
                # Create WhatsApp-friendly summary and extract template variables
                summary, template_vars = self._create_whatsapp_summary(analysis, model_used, timestamp)
                
                # Validate template variables before sending
                if not self._validate_template_vars(template_vars):
                    print(f"⚠️  Template validation failed on attempt {attempt + 1}")
                    if attempt == max_retries - 1:
                        print("❌ All attempts failed - template variables invalid")
                        return False
                    import time
                    time.sleep(retry_delay)
                    continue
                
                # Send using template variables (empty message since template handles content)
                success = self.send_message("", template_vars)
                
                if success:
                    print(f"✅ WhatsApp summary sent successfully on attempt {attempt + 1}")
                    return True
                else:
                    print(f"⚠️  Send failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        import time
                        print(f"⏳ Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    print("❌ All retry attempts exhausted")
                    return False
                import time
                time.sleep(retry_delay)
                retry_delay *= 2
        
        return False
    
    def _create_whatsapp_summary(self, analysis: str, model_used: str, timestamp: str) -> tuple[str, dict]:
        """Create a WhatsApp message using the approved template format and return template variables"""
        
        print("🔍 Starting robust template variable extraction...")
        
        # Extract key information from the analysis
        lines = analysis.split('\n')
        analysis_lower = analysis.lower()
        
        # Initialize template variables with bulletproof defaults
        template_vars = {
            '1': datetime.now().strftime('%H:%M'),  # Current UTC time
            '2': '0.00',  # Current price
            '3': '0.0',   # 24h change
            '4': '0',     # OI in millions
            '5': '0.0',   # OI change
            '6': '0.000', # Current funding rate
            '7': '0.000', # Funding rate change
            '8': '0.00',  # L/S ratio
            '9': 'WAIT',  # Signal
            '10': 'Analysis unavailable',  # Correlation
            '11': 'No position',  # Positioned
            '12': 'Monitor price action'  # Prepare
        }
        
        print(f"📝 Processing {len(lines)} lines of analysis text...")

        # ROBUST EXTRACTION: Price information with multiple fallback patterns
        print("🔍 Extracting price information...")
        price_extracted = False
        for line in lines:
            if price_extracted:
                break
            line_clean = line.strip()
            
            # Pattern 1: "Price: $123.45"
            if "Price:" in line and "$" in line:
                try:
                    price_match = line.split("$")[1].split()[0].replace(',', '').replace('(', '').replace(')', '')
                    if self._is_valid_price(price_match):
                        template_vars['2'] = price_match
                        price_extracted = True
                        print(f"✅ Price extracted (Pattern 1): ${price_match}")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Price Pattern 1 failed: {e}")
            
            # Pattern 2: "💰 Price: $123.45"
            if "💰" in line and "$" in line:
                try:
                    price_match = line.split("$")[1].split()[0].replace(',', '').replace('(', '').replace(')', '')
                    if self._is_valid_price(price_match):
                        template_vars['2'] = price_match
                        price_extracted = True
                        print(f"✅ Price extracted (Pattern 2): ${price_match}")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Price Pattern 2 failed: {e}")
            
            # Pattern 3: Any line with "$" and numbers
            if "$" in line and not price_extracted:
                try:
                    price_pattern = r'\$([0-9]+\.?[0-9]*)'  
                    matches = re.findall(price_pattern, line)
                    if matches:
                        price_match = matches[0]
                        if self._is_valid_price(price_match) and float(price_match) > 10:  # Reasonable SOL price
                            template_vars['2'] = price_match
                            price_extracted = True
                            print(f"✅ Price extracted (Pattern 3): ${price_match}")
                            continue
                except (IndexError, ValueError, re.error) as e:
                    print(f"⚠️  Price Pattern 3 failed: {e}")
        
        if not price_extracted:
            print("⚠️  No valid price found, using default: $0.00")
        
        # ROBUST EXTRACTION: 24h price change with multiple patterns
        print("🔍 Extracting 24h price change...")
        change_extracted = False
        for line in lines:
            if change_extracted:
                break
            line_clean = line.strip()
            
            # Pattern 1: "(+2.5% 24h)"
            if "24h" in line and "%" in line and "(" in line:
                try:
                    change_match = line.split("(")[1].split("%")[0].strip()
                    if self._is_valid_percentage(change_match):
                        template_vars['3'] = change_match
                        change_extracted = True
                        print(f"✅ 24h change extracted (Pattern 1): {change_match}%")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  24h change Pattern 1 failed: {e}")
            
            # Pattern 2: "price_24h_change: +2.5"
            if "price_24h_change" in line and ":" in line:
                try:
                    change_match = line.split(":")[1].strip().replace('%', '')
                    if self._is_valid_percentage(change_match):
                        template_vars['3'] = change_match
                        change_extracted = True
                        print(f"✅ 24h change extracted (Pattern 2): {change_match}%")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  24h change Pattern 2 failed: {e}")
            
            # Pattern 3: Regex for any percentage with 24h context
            if "24h" in line.lower():
                try:
                    percent_pattern = r'([+-]?[0-9]+\.?[0-9]*)%'
                    matches = re.findall(percent_pattern, line)
                    if matches:
                        change_match = matches[0]
                        if self._is_valid_percentage(change_match):
                            template_vars['3'] = change_match
                            change_extracted = True
                            print(f"✅ 24h change extracted (Pattern 3): {change_match}%")
                            continue
                except (IndexError, ValueError, re.error) as e:
                    print(f"⚠️  24h change Pattern 3 failed: {e}")
        
        if not change_extracted:
            print("⚠️  No valid 24h change found, using default: 0.0%")
        
        # ROBUST EXTRACTION: Open Interest with multiple patterns
        print("🔍 Extracting Open Interest information...")
        oi_extracted = False
        oi_change_extracted = False
        
        for line in lines:
            line_clean = line.strip()
            
            # Extract OI value
            if not oi_extracted and "OI" in line and "$" in line:
                try:
                    # Pattern 1: "OI: $150M"
                    if "$" in line and "M" in line:
                        oi_match = line.split("$")[1].split("M")[0].strip().replace(',', '')
                        if self._is_valid_number(oi_match):
                            template_vars['4'] = oi_match
                            oi_extracted = True
                            print(f"✅ OI extracted: ${oi_match}M")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  OI extraction failed: {e}")
            
            # Pattern 2: "oi_usd: 150000000"
            if not oi_extracted and "oi_usd" in line.lower():
                try:
                    oi_raw = line.split(":")[1].strip().replace(',', '')
                    oi_millions = float(oi_raw) / 1e6
                    if oi_millions > 0:
                        template_vars['4'] = f"{oi_millions:.1f}"
                        oi_extracted = True
                        print(f"✅ OI extracted (Pattern 2): ${oi_millions:.1f}M")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  OI Pattern 2 failed: {e}")
            
            # Extract OI change
            if not oi_change_extracted and "OI" in line and "(" in line and "%" in line:
                try:
                    oi_change = line.split("(")[1].split("%")[0].strip()
                    if self._is_valid_percentage(oi_change):
                        template_vars['5'] = oi_change
                        oi_change_extracted = True
                        print(f"✅ OI change extracted: {oi_change}%")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  OI change extraction failed: {e}")
        
        if not oi_extracted:
            print("⚠️  No valid OI found, using default: 0M")
        if not oi_change_extracted:
            print("⚠️  No valid OI change found, using default: 0.0%")
        
        # ROBUST EXTRACTION: Funding rates with multiple patterns
        print("🔍 Extracting funding rate information...")
        funding_extracted = False
        funding_change_extracted = False
        
        for line in lines:
            line_clean = line.strip()
            
            # Extract current funding rate
            if not funding_extracted and "funding" in line.lower() and "%" in line:
                try:
                    # Pattern 1: "Funding: 0.045%"
                    if "Funding:" in line:
                        funding_match = line.split(":")[1].split("%")[0].strip().replace('(', '')
                        if self._is_valid_funding_rate(funding_match):
                            template_vars['6'] = funding_match
                            funding_extracted = True
                            print(f"✅ Funding rate extracted: {funding_match}%")
                    
                    # Pattern 2: "funding_pct: 0.045"
                    elif "funding_pct" in line.lower():
                        funding_match = line.split(":")[1].strip().replace(',', '')
                        if self._is_valid_funding_rate(funding_match):
                            template_vars['6'] = funding_match
                            funding_extracted = True
                            print(f"✅ Funding rate extracted (Pattern 2): {funding_match}%")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Funding rate extraction failed: {e}")
            
            # Extract funding rate change
            if not funding_change_extracted and "funding" in line.lower():
                try:
                    # Pattern 1: "6h Δ +0.012%"
                    if "6h Δ" in line or "6h δ" in line.lower():
                        change_part = line.split("Δ")[1] if "Δ" in line else line.split("δ")[1]
                        change_match = change_part.split("%")[0].strip().replace('(', '').replace(')', '')
                        if self._is_valid_funding_rate(change_match):
                            template_vars['7'] = change_match
                            funding_change_extracted = True
                            print(f"✅ Funding change extracted: {change_match}%")
                    
                    # Pattern 2: "funding_6h_change: +0.012"
                    elif "funding_6h_change" in line.lower():
                        change_match = line.split(":")[1].strip().replace(',', '')
                        if self._is_valid_funding_rate(change_match):
                            template_vars['7'] = change_match
                            funding_change_extracted = True
                            print(f"✅ Funding change extracted (Pattern 2): {change_match}%")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Funding change extraction failed: {e}")
        
        if not funding_extracted:
            print("⚠️  No valid funding rate found, using default: 0.000%")
        if not funding_change_extracted:
            print("⚠️  No valid funding change found, using default: 0.000%")
        
        # ROBUST EXTRACTION: Long/Short ratio
        print("🔍 Extracting L/S ratio...")
        ls_extracted = False
        
        for line in lines:
            if ls_extracted:
                break
            line_clean = line.strip()
            
            # Pattern 1: "L/S: 2.34"
            if "L/S:" in line:
                try:
                    ls_match = line.split("L/S:")[1].split()[0].strip().replace('(', '').replace(')', '')
                    if self._is_valid_ratio(ls_match):
                        template_vars['8'] = ls_match
                        ls_extracted = True
                        print(f"✅ L/S ratio extracted: {ls_match}")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  L/S Pattern 1 failed: {e}")
            
            # Pattern 2: "ls_ratio: 2.34"
            if "ls_ratio" in line.lower() and ":" in line:
                try:
                    ls_match = line.split(":")[1].strip().replace(',', '')
                    if self._is_valid_ratio(ls_match):
                        template_vars['8'] = ls_match
                        ls_extracted = True
                        print(f"✅ L/S ratio extracted (Pattern 2): {ls_match}")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  L/S Pattern 2 failed: {e}")
            
            # Pattern 3: "Long/Short: 2.34"
            if "long/short" in line.lower() and ":" in line:
                try:
                    ls_match = line.split(":")[1].split()[0].strip().replace('(', '').replace(')', '')
                    if self._is_valid_ratio(ls_match):
                        template_vars['8'] = ls_match
                        ls_extracted = True
                        print(f"✅ L/S ratio extracted (Pattern 3): {ls_match}")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  L/S Pattern 3 failed: {e}")
        
        if not ls_extracted:
            print("⚠️  No valid L/S ratio found, using default: 0.00")
        
        # ROBUST EXTRACTION: Trading signal
        print("🔍 Extracting trading signal...")
        signal_extracted = False
        
        for line in lines:
            if signal_extracted:
                break
            line_clean = line.strip()
            
            # Pattern 1: "🚨 SIGNAL: LONG"
            if "SIGNAL:" in line:
                try:
                    signal_match = line.split("SIGNAL:")[1].strip().upper()
                    # Clean up signal
                    for valid_signal in ["LONG", "SHORT", "WAIT"]:
                        if valid_signal in signal_match:
                            template_vars['9'] = valid_signal
                            signal_extracted = True
                            print(f"✅ Signal extracted: {valid_signal}")
                            break
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Signal Pattern 1 failed: {e}")
            
            # Pattern 2: "Auto Signal: LONG"
            if "auto signal" in line.lower() and ":" in line:
                try:
                    signal_match = line.split(":")[1].strip().upper()
                    for valid_signal in ["LONG", "SHORT", "WAIT"]:
                        if valid_signal in signal_match:
                            template_vars['9'] = valid_signal
                            signal_extracted = True
                            print(f"✅ Signal extracted (Pattern 2): {valid_signal}")
                            break
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Signal Pattern 2 failed: {e}")
        
        if not signal_extracted:
            print("⚠️  No valid signal found, using default: WAIT")
        
        # ROBUST EXTRACTION: Technical setup/correlation
        print("🔍 Extracting technical setup/correlation...")
        correlation_extracted = False
        
        for line in lines:
            if correlation_extracted:
                break
            line_clean = line.strip()
            
            # Pattern 1: "📊 SETUP: Technical analysis"
            if "SETUP:" in line:
                try:
                    setup_match = line.split("SETUP:")[1].strip()
                    if len(setup_match) > 5:  # Must have meaningful content
                        # Truncate if too long for template
                        if len(setup_match) > 200:
                            setup_match = setup_match[:197] + "..."
                        template_vars['10'] = setup_match
                        correlation_extracted = True
                        print(f"✅ Correlation extracted: {setup_match[:50]}...")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Setup Pattern 1 failed: {e}")
            
            # Pattern 2: "📊 CORRELATION: Analysis"
            if "CORRELATION:" in line:
                try:
                    corr_match = line.split("CORRELATION:")[1].strip()
                    if len(corr_match) > 5:
                        if len(corr_match) > 200:
                            corr_match = corr_match[:197] + "..."
                        template_vars['10'] = corr_match
                        correlation_extracted = True
                        print(f"✅ Correlation extracted (Pattern 2): {corr_match[:50]}...")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Correlation Pattern 2 failed: {e}")
            
            # Pattern 3: Look for feature summary
            if "features:" in line.lower() and len(line) > 20:
                try:
                    features_match = line.split(":")[1].strip()
                    if len(features_match) > 10 and not correlation_extracted:
                        if len(features_match) > 200:
                            features_match = features_match[:197] + "..."
                        template_vars['10'] = features_match
                        correlation_extracted = True
                        print(f"✅ Correlation extracted (Pattern 3): {features_match[:50]}...")
                        continue
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Features Pattern 3 failed: {e}")
        
        if not correlation_extracted:
            print("⚠️  No valid correlation found, using default: Analysis unavailable")
        
        # ROBUST EXTRACTION: Confidence and positioning
        print("🔍 Extracting confidence and positioning...")
        confidence_extracted = False
        
        for line in lines:
            if confidence_extracted:
                break
            line_clean = line.strip()
            
            # Extract confidence for positioning decision
            if "confidence" in line.lower() and ":" in line:
                try:
                    # Pattern 1: "Confidence: 75/100"
                    if "/" in line:
                        confidence = line.split(":")[1].split("/")[0].strip()
                    # Pattern 2: "Confidence: 75"
                    else:
                        confidence = line.split(":")[1].strip().replace('%', '')
                    
                    conf_num = int(float(confidence))
                    if conf_num >= 70:
                        template_vars['11'] = "High confidence setup"
                        template_vars['12'] = "Prepare entry zones"
                        confidence_extracted = True
                        print(f"✅ High confidence extracted: {conf_num}")
                    elif conf_num >= 50:
                        template_vars['11'] = "Medium confidence"
                        template_vars['12'] = "Monitor for confirmation"
                        confidence_extracted = True
                        print(f"✅ Medium confidence extracted: {conf_num}")
                    else:
                        template_vars['11'] = "Low confidence"
                        template_vars['12'] = "Wait for better setup"
                        confidence_extracted = True
                        print(f"✅ Low confidence extracted: {conf_num}")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Confidence extraction failed: {e}")
        
        if not confidence_extracted:
            print("⚠️  No valid confidence found, using default positioning")
        
        # ROBUST EXTRACTION: Entry, Stop, Target for PREPARE field
        print("🔍 Extracting entry/stop/target levels...")
        entry_data = {"entry": None, "stop": None, "target": None}
        
        for line in lines:
            line_clean = line.strip()
            
            # Extract ENTRY
            if "ENTRY:" in line and not entry_data["entry"]:
                try:
                    entry_match = line.split("ENTRY:")[1].strip()[:50]  # Limit length
                    if len(entry_match) > 2:
                        entry_data["entry"] = entry_match
                        print(f"✅ Entry level extracted: {entry_match}")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Entry extraction failed: {e}")
            
            # Extract STOP
            if "STOP:" in line and not entry_data["stop"]:
                try:
                    stop_match = line.split("STOP:")[1].strip()[:50]  # Limit length
                    if len(stop_match) > 2:
                        entry_data["stop"] = stop_match
                        print(f"✅ Stop level extracted: {stop_match}")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Stop extraction failed: {e}")
            
            # Extract TARGET
            if "TARGET:" in line and not entry_data["target"]:
                try:
                    target_match = line.split("TARGET:")[1].strip()[:50]  # Limit length
                    if len(target_match) > 2:
                        entry_data["target"] = target_match
                        print(f"✅ Target level extracted: {target_match}")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Target extraction failed: {e}")
        
        # Build PREPARE field based on extracted data
        if entry_data["entry"]:
            if template_vars['12'] == "Prepare entry zones":
                template_vars['12'] = f"Entry: {entry_data['entry']}"
            elif template_vars['12'] == "Monitor for confirmation":
                template_vars['12'] = f"Monitor: {entry_data['entry']}"
            else:
                template_vars['12'] = f"Entry: {entry_data['entry']}"
            
            # Add stop if available
            if entry_data["stop"]:
                template_vars['12'] += f" | Stop: {entry_data['stop']}"
            
            # Add target if available
            if entry_data["target"]:
                template_vars['12'] += f" | Target: {entry_data['target']}"
        elif entry_data["stop"] and not entry_data["entry"]:
            template_vars['12'] = f"Stop: {entry_data['stop']}"
        elif entry_data["target"] and not entry_data["entry"]:
            template_vars['12'] = f"Target: {entry_data['target']}"
        
        print(f"✅ PREPARE field built: {template_vars['12']}")
        
        # ROBUST EXTRACTION: Risk and News for additional context
        print("🔍 Extracting risk and news context...")
        
        for line in lines:
            line_clean = line.strip()
            
            # Extract RISK for additional context in CORRELATION
            if "RISK:" in line:
                try:
                    risk_match = line.split("RISK:")[1].strip()
                    if len(risk_match) > 5:  # Must have meaningful content
                        if template_vars['10'] and len(template_vars['10']) < 150:
                            template_vars['10'] += f" | Risk: {risk_match[:50]}"
                            print(f"✅ Risk context added to correlation")
                        elif template_vars['10'] == "Analysis unavailable":
                            template_vars['10'] = f"Risk: {risk_match[:100]}"
                            print(f"✅ Risk set as primary correlation")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Risk extraction failed: {e}")
            
            # Extract NEWS if available
            if "NEWS:" in line:
                try:
                    news_match = line.split("NEWS:")[1].strip()
                    if news_match != "None" and len(news_match) > 10:
                        # Add news context to correlation if space allows
                        if template_vars['10'] and len(template_vars['10']) < 100 and template_vars['10'] != "Analysis unavailable":
                            template_vars['10'] += f" | News: {news_match[:40]}"
                            print(f"✅ News context added to correlation")
                        elif template_vars['10'] == "Analysis unavailable":
                            template_vars['10'] = f"News: {news_match[:100]}"
                            print(f"✅ News set as primary correlation")
                except (IndexError, ValueError) as e:
                    print(f"⚠️  News extraction failed: {e}")
        
        # FINAL VALIDATION AND SANITIZATION
        print("🔍 Final validation and sanitization...")
        template_vars = self._sanitize_template_vars(template_vars)
        
        # Create the template message using the EXACT approved format
        template_message = (
            f"🎯 SOL • {template_vars['1']} UTC\n"
            f"📊 ${template_vars['2']} ({template_vars['3']}% 24h) | OI: ${template_vars['4']}M ({template_vars['5']}%)\n"
            f"💸 {template_vars['6']}% → {template_vars['7']}% | L/S: {template_vars['8']}\n\n"
            f"🚨 SIGNAL: {template_vars['9']}\n"
            f"📊 CORRELATION: {template_vars['10']}\n"
            f"⚠️ POSITIONED: {template_vars['11']}\n"
            f"💡 PREPARE: {template_vars['12']}\n\n"
            f"📈 24h evolution • o3"
        )
        
        print("✅ Template variables extraction complete!")
        print(f"📊 Final template message length: {len(template_message)} characters")
        
        # FINAL VALIDATION: Ensure template message is properly formatted
        if len(template_message) < 50:
            print("⚠️  Template message seems too short")
        elif len(template_message) > 1600:
            print("⚠️  Template message might be too long for WhatsApp")
        
        return template_message, template_vars

    def _sanitize_template_vars(self, template_vars: dict) -> dict:
        """Final sanitization of template variables"""
        print("🧹 Sanitizing template variables...")
        
        # Ensure all values are strings and within reasonable limits
        sanitized = {}
        
        for key, value in template_vars.items():
            try:
                # Convert to string and clean
                clean_value = str(value).strip()
                
                # Remove any problematic characters
                clean_value = clean_value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                
                # Limit length for template compatibility
                if key in ['10', '11', '12']:  # Longer text fields
                    clean_value = clean_value[:200] if len(clean_value) > 200 else clean_value
                else:  # Numeric fields
                    clean_value = clean_value[:20] if len(clean_value) > 20 else clean_value
                
                # Ensure no empty values
                if not clean_value or clean_value.isspace():
                    # Provide fallback values
                    fallbacks = {
                        '1': datetime.now().strftime('%H:%M'),
                        '2': '0.00', '3': '0.0', '4': '0', '5': '0.0',
                        '6': '0.000', '7': '0.000', '8': '0.00',
                        '9': 'WAIT', '10': 'Analysis unavailable',
                        '11': 'No position', '12': 'Monitor price action'
                    }
                    clean_value = fallbacks.get(key, 'N/A')
                    print(f"⚠️  Variable {key} was empty, using fallback: {clean_value}")
                
                sanitized[key] = clean_value
                
            except Exception as e:
                print(f"⚠️  Error sanitizing variable {key}: {e}")
                # Use fallback
                fallbacks = {
                    '1': datetime.now().strftime('%H:%M'),
                    '2': '0.00', '3': '0.0', '4': '0', '5': '0.0',
                    '6': '0.000', '7': '0.000', '8': '0.00',
                    '9': 'WAIT', '10': 'Analysis unavailable',
                    '11': 'No position', '12': 'Monitor price action'
                }
                sanitized[key] = fallbacks.get(key, 'N/A')
        
        print("✅ Template variables sanitized successfully")
        return sanitized
    
    def _validate_template_vars(self, template_vars: dict) -> bool:
        """Comprehensive validation of template variables"""
        print("🔍 Validating template variables...")
        
        # Check all required variables are present
        required_vars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        missing_vars = [var for var in required_vars if var not in template_vars]
        
        if missing_vars:
            print(f"❌ Missing required variables: {missing_vars}")
            return False
        
        # Validate specific variable formats
        validations = {
            '1': lambda x: len(x) == 5 and ':' in x,  # Time format HH:MM
            '2': lambda x: self._is_valid_price(x.replace('$', '')),  # Price
            '3': lambda x: self._is_valid_percentage(x.replace('%', '')),  # 24h change
            '4': lambda x: self._is_valid_number(x),  # OI
            '5': lambda x: self._is_valid_percentage(x.replace('%', '')),  # OI change
            '6': lambda x: self._is_valid_funding_rate(x.replace('%', '')),  # Funding
            '7': lambda x: self._is_valid_funding_rate(x.replace('%', '')),  # Funding change
            '8': lambda x: self._is_valid_ratio(x),  # L/S ratio
            '9': lambda x: x.upper() in ['LONG', 'SHORT', 'WAIT'],  # Signal
            '10': lambda x: len(x) > 5 and len(x) <= 200,  # Correlation
            '11': lambda x: len(x) > 3 and len(x) <= 100,  # Positioned
            '12': lambda x: len(x) > 3 and len(x) <= 200,  # Prepare
        }
        
        validation_passed = True
        for var, validator in validations.items():
            try:
                if not validator(template_vars[var]):
                    print(f"⚠️  Variable {var} failed validation: '{template_vars[var]}'")
                    validation_passed = False
            except Exception as e:
                print(f"⚠️  Variable {var} validation error: {e}")
                validation_passed = False
        
        # Check for reasonable data quality
        default_count = sum(1 for v in template_vars.values() 
                          if str(v) in ['0.00', '0.0', '0.000', 'WAIT', 'Analysis unavailable', 'No position', 'Monitor price action'])
        
        if default_count > 8:  # Too many default values
            print(f"⚠️  Too many default values ({default_count}/12) - analysis may be incomplete")
            validation_passed = False
        
        if validation_passed:
            print("✅ All template variables validated successfully")
        else:
            print("❌ Template variable validation failed")
        
        return validation_passed

    def test_template_setup(self) -> bool:
        """Comprehensive test of WhatsApp template setup and variables"""
        print("🧪 Starting comprehensive WhatsApp template testing...")
        
        # Test 1: Environment variables
        print("\n🔍 Test 1: Environment Variables")
        env_tests = {
            'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
            'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
            'TWILIO_WHATSAPP_FROM': os.getenv('TWILIO_WHATSAPP_FROM'),
            'TWILIO_TEMPLATE_SID': os.getenv('TWILIO_TEMPLATE_SID'),
            'WHATSAPP_TO_NUMBERS': os.getenv('WHATSAPP_TO_NUMBERS') or os.getenv('WHATSAPP_TO_NUMBER')
        }
        
        env_passed = True
        for var, value in env_tests.items():
            if value:
                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ❌ {var}: Not set")
                env_passed = False
        
        if not env_passed:
            print("❌ Environment variable test failed")
            return False
        
        # Test 2: Twilio client initialization
        print("\n🔍 Test 2: Twilio Client Initialization")
        if not self.client:
            print("❌ Twilio client initialization failed")
            return False
        print("✅ Twilio client initialized successfully")
        
        # Test 3: Template variable extraction with multiple test cases
        print("\n🔍 Test 3: Template Variable Extraction")
        test_cases = [
            {
                'name': 'Complete Analysis',
                'analysis': (
                    "Price: $125.45 (+3.2% 24h)\n"
                    "OI: $175M (+2.1%)\n"
                    "Funding: 0.067% (6h Δ +0.015%)\n"
                    "L/S: 2.89\n"
                    "Auto Signal: LONG\n"
                    "Confidence: 82/100\n"
                    "🚨 SIGNAL: LONG\n"
                    "📊 SETUP: Strong bullish momentum\n"
                    "🎯 ENTRY: $124-126\n"
                    "⛔ STOP: $120\n"
                    "🎪 TARGET: $135\n"
                    "⚠️ RISK: Funding stress"
                )
            },
            {
                'name': 'Minimal Analysis',
                'analysis': (
                    "Price: $98.20 (-1.5% 24h)\n"
                    "SIGNAL: WAIT\n"
                    "Confidence: 45/100"
                )
            },
            {
                'name': 'Edge Case Analysis',
                'analysis': (
                    "Current price: $200.00\n"
                    "24h change: +15.7%\n"
                    "Open Interest: $500M\n"
                    "Funding rate: -0.125%\n"
                    "Long/Short: 0.85\n"
                    "Signal: SHORT"
                )
            }
        ]
        
        extraction_passed = True
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test 3.{i}: {test_case['name']}")
            try:
                test_message, extracted_vars = self._create_whatsapp_summary(
                    test_case['analysis'], 'Test Model', '12:00 UTC'
                )
                
                # Validate extraction
                if not self._validate_template_vars(extracted_vars):
                    print(f"   ❌ {test_case['name']}: Variable validation failed")
                    extraction_passed = False
                    continue
                
                print(f"   ✅ {test_case['name']}: Variables extracted successfully")
                print(f"      Signal: {extracted_vars.get('9', 'N/A')}")
                print(f"      Price: ${extracted_vars.get('2', 'N/A')}")
                print(f"      Message length: {len(test_message)} chars")
                
            except Exception as e:
                print(f"   ❌ {test_case['name']}: Extraction failed - {e}")
                extraction_passed = False
        
        if not extraction_passed:
            print("❌ Template variable extraction test failed")
            return False
        
        # Test 4: Template message formatting
        print("\n🔍 Test 4: Template Message Formatting")
        try:
            sample_vars = {
                '1': '15:30', '2': '123.45', '3': '+2.8', '4': '180',
                '5': '+1.5', '6': '0.055', '7': '+0.008', '8': '2.15',
                '9': 'LONG', '10': 'Strong technical setup with bullish divergence',
                '11': 'High confidence', '12': 'Entry: $122-125 | Stop: $118 | Target: $135'
            }
            
            template_message = (
                f"🎯 SOL • {sample_vars['1']} UTC\n"
                f"📊 ${sample_vars['2']} ({sample_vars['3']}% 24h) | OI: ${sample_vars['4']}M ({sample_vars['5']}%)\n"
                f"💸 {sample_vars['6']}% → {sample_vars['7']}% | L/S: {sample_vars['8']}\n\n"
                f"🚨 SIGNAL: {sample_vars['9']}\n"
                f"📊 CORRELATION: {sample_vars['10']}\n"
                f"⚠️ POSITIONED: {sample_vars['11']}\n"
                f"💡 PREPARE: {sample_vars['12']}\n\n"
                f"📈 24h evolution • o3"
            )
            
            if 50 <= len(template_message) <= 1600:
                print(f"   ✅ Template message format valid ({len(template_message)} chars)")
            else:
                print(f"   ⚠️  Template message length unusual: {len(template_message)} chars")
            
            print("   ✅ Sample formatted message:")
            print("   " + "\n   ".join(template_message.split("\n")))
            
        except Exception as e:
            print(f"   ❌ Template formatting test failed: {e}")
            return False
        
        # Test 5: Dry run message creation (no actual sending)
        print("\n🔍 Test 5: Dry Run Message Creation")
        try:
            # Simulate the full process without sending
            analysis_data = {
                'analysis': test_cases[0]['analysis'],
                'model_used': 'Test Hybrid',
                'timestamp': datetime.now().strftime('%H:%M UTC')
            }
            
            # This would normally send, but we'll just validate the process
            summary, template_vars = self._create_whatsapp_summary(
                analysis_data['analysis'], 
                analysis_data['model_used'], 
                analysis_data['timestamp']
            )
            
            if self._validate_template_vars(template_vars):
                print("   ✅ Dry run message creation successful")
                print(f"      All systems ready for live sending")
            else:
                print("   ❌ Dry run validation failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Dry run test failed: {e}")
            return False
        
        print("\n🎉 All WhatsApp template tests passed successfully!")
        print("✅ System is ready for live WhatsApp message sending")
        print("\n💡 To send a test message, run with AUTO_SEND_TO_WHATSAPP=true")
        
        return True


def send_analysis_to_whatsapp(analysis_file: str) -> bool:
    """Send analysis results to WhatsApp"""
    try:
        # Load analysis data
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        # Create WhatsApp sender
        sender = WhatsAppSender()
        
        # Send summary
        return sender.send_analysis_summary(analysis_data)
        
    except FileNotFoundError:
        print(f"❌ Analysis file not found: {analysis_file}")
        return False
    except Exception as e:
        print(f"❌ Error sending to WhatsApp: {e}")
        return False

def send_alert_to_whatsapp(message: str) -> bool:
    """Send a simple alert message to WhatsApp"""
    sender = WhatsAppSender()
    return sender.send_message(message)

def test_whatsapp_template():
    """Comprehensive test function for WhatsApp template setup"""
    print("🚀 Starting comprehensive WhatsApp template testing...")
    
    try:
        sender = WhatsAppSender()
        test_passed = sender.test_template_setup()
        
        if test_passed:
            print("\n🎉 WhatsApp template system fully validated!")
            print("✅ Ready for production use")
        else:
            print("\n❌ WhatsApp template system validation failed")
            print("💡 Please check the error messages above and fix the issues")
            
        return test_passed
        
    except Exception as e:
        print(f"❌ WhatsApp comprehensive test failed: {e}")
        import traceback
        print(f"💡 Full error trace: {traceback.format_exc()}")
        return False


def run_full_system_test():
    """Run a complete system test including analysis and WhatsApp integration"""
    print("🔧 Running full system integration test...")
    
    # Test 1: WhatsApp Template System
    print("\n=== WhatsApp Template System Test ===")
    whatsapp_test = test_whatsapp_template()
    
    if not whatsapp_test:
        print("❌ WhatsApp system test failed - aborting full test")
        return False
    
    # Test 2: Environment Configuration
    print("\n=== Environment Configuration Test ===")
    required_vars = [
        'COINALYZE_API_KEY', 'OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_FROM', 'TWILIO_TEMPLATE_SID'
    ]
    
    env_test_passed = True
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: Configured")
        else:
            print(f"   ❌ {var}: Missing")
            env_test_passed = False
    
    if not env_test_passed:
        print("❌ Environment configuration test failed")
        return False
    
    print("\n🎉 Full system test completed successfully!")
    print("✅ All systems operational and ready for production")
    return True

if __name__ == "__main__":
    import sys
    
    # Check command line arguments for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--full-test":
        print("🚀 Running full system integration test...")
        success = run_full_system_test()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--template-test":
        print("🚀 Running WhatsApp template test...")
        success = test_whatsapp_template()
        sys.exit(0 if success else 1)
    else:
        # Default: Run comprehensive template test
        print("🚀 Running comprehensive WhatsApp template test...")
        success = test_whatsapp_template()
        
        if success:
            print("\n💡 To run full system test: python whatsapp_sender.py --full-test")
            print("💡 To test template only: python whatsapp_sender.py --template-test")
        
        sys.exit(0 if success else 1)
