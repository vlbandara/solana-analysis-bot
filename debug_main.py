#!/usr/bin/env python3

# Add debugging to the main script
with open('o3_enhanced_solana_agent.py', 'r') as f:
    content = f.read()

# Add debug prints around WhatsApp integration
debug_whatsapp = '''
    print("\\n💾 Full analysis saved to o3_enhanced_analysis.json")
    
    # 🆕 WHATSAPP INTEGRATION
    print("\\n📱 Sending analysis to WhatsApp group...")
    print("🔍 DEBUG: Checking if analysis file exists...")
    import os
    if os.path.exists('o3_enhanced_analysis.json'):
        print("✅ DEBUG: Analysis file found")
        print("🔍 DEBUG: File size:", os.path.getsize('o3_enhanced_analysis.json'), "bytes")
    else:
        print("❌ DEBUG: Analysis file not found!")
    
    print("🔍 DEBUG: About to call send_analysis_to_whatsapp...")
    whatsapp_success = send_analysis_to_whatsapp('o3_enhanced_analysis.json')
    print(f"🔍 DEBUG: WhatsApp result: {whatsapp_success}")
    
    if whatsapp_success:
        print("✅ WhatsApp integration successful!")
    else:
        print("⚠️ WhatsApp integration failed - check credentials")
'''

# Replace the WhatsApp integration section
content = content.replace(
    '    print("\\n💾 Full analysis saved to o3_enhanced_analysis.json")\n    \n    # 🆕 WHATSAPP INTEGRATION\n    print("\\n📱 Sending analysis to WhatsApp group...")\n    whatsapp_success = send_analysis_to_whatsapp(\'o3_enhanced_analysis.json\')\n    \n    if whatsapp_success:\n        print("✅ WhatsApp integration successful!")\n    else:\n        print("⚠️ WhatsApp integration failed - check credentials")',
    debug_whatsapp
)

# Write back
with open('o3_enhanced_solana_agent.py', 'w') as f:
    f.write(content)

print("Added debugging to o3_enhanced_solana_agent.py")
