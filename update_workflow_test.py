#!/usr/bin/env python3

# Read the workflow file
with open('.github/workflows/solana-analysis.yml', 'r') as f:
    content = f.read()

# Add WhatsApp test step
new_step = '''
      - name: Test WhatsApp Integration
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TWILIO_ACCOUNT_SID: ${{ secrets.TWILIO_ACCOUNT_SID }}
          TWILIO_AUTH_TOKEN: ${{ secrets.TWILIO_AUTH_TOKEN }}
          TWILIO_WHATSAPP_FROM: ${{ secrets.TWILIO_WHATSAPP_FROM }}
          WHATSAPP_TO_NUMBER: ${{ secrets.WHATSAPP_TO_NUMBER }}
        run: |
          uv run python test_whatsapp.py

      - name: Run o3 Enhanced Solana Analysis
'''

# Replace the analysis step
content = content.replace(
    '      - name: Run o3 Enhanced Solana Analysis\n        env:\n          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}\n          TWILIO_ACCOUNT_SID: ${{ secrets.TWILIO_ACCOUNT_SID }}\n          TWILIO_AUTH_TOKEN: ${{ secrets.TWILIO_AUTH_TOKEN }}\n          TWILIO_WHATSAPP_FROM: ${{ secrets.TWILIO_WHATSAPP_FROM }}\n          WHATSAPP_TO_NUMBER: ${{ secrets.WHATSAPP_TO_NUMBER }}\n        run: |\n          uv run python o3_enhanced_solana_agent.py',
    new_step
)

# Write back
with open('.github/workflows/solana-analysis.yml', 'w') as f:
    f.write(content)

print("Updated GitHub Actions workflow with WhatsApp test")
