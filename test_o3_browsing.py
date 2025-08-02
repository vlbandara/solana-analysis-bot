#!/usr/bin/env python3
"""
Simple test to verify if o3 model can use web_search_preview tool
"""

import os
from openai import OpenAI

def test_o3_browsing():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("🧪 Testing o3 model with web search capability...")
    
    try:
        # Direct test - ask for current BTC price
        response = client.responses.create(
            model="o3",
            tools=[{"type": "web_search_preview"}],
            input="What is the current Bitcoin (BTC) price right now? Please search the web for the latest BTC/USD price and tell me the exact number."
        )
        
        print("\n" + "="*60)
        print("🔍 O3 MODEL RESPONSE WITH WEB SEARCH:")
        print("="*60)
        print(response.output_text)
        print("\n" + "="*60)
        
        # Check if response contains realistic BTC price (should be >$100k)
        response_text = response.output_text.lower()
        if "100" in response_text or "110" in response_text or "114" in response_text:
            print("✅ SUCCESS: Model appears to be using web search (realistic BTC price)")
        elif "60" in response_text or "69" in response_text:
            print("❌ FAILURE: Model is hallucinating (outdated BTC price)")
        else:
            print("⚠️ UNCLEAR: Check the response manually")
            
        return response.output_text
        
    except Exception as e:
        print(f"❌ Error testing o3 browsing: {e}")
        return None

def test_fallback_gpt4():
    """Test with GPT-4 that definitely supports web search"""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("\n🧪 Testing GPT-4 with web search for comparison...")
    
    try:
        # Use regular chat completions with GPT-4 + web search
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What is the current Bitcoin (BTC) price right now? Please search for the latest BTC/USD price."}
            ],
            tools=[{"type": "web_search_preview"}]
        )
        
        print("\n" + "="*60)
        print("🔍 GPT-4o-mini RESPONSE WITH WEB SEARCH:")
        print("="*60)
        print(response.choices[0].message.content)
        print("\n" + "="*60)
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error testing GPT-4 browsing: {e}")
        return None

if __name__ == "__main__":
    print("🚀 TESTING AI MODEL BROWSING CAPABILITIES")
    print("="*60)
    
    # Test o3 first
    o3_result = test_o3_browsing()
    
    # Test GPT-4 for comparison
    gpt4_result = test_fallback_gpt4()
    
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print("="*60)
    print(f"o3 with web search: {'✅ Working' if o3_result and ('100' in o3_result or '110' in o3_result) else '❌ Not working'}")
    print(f"GPT-4o-mini with web search: {'✅ Working' if gpt4_result else '❌ Not working'}")
    print("\nIf o3 is not using web search, we need to manually inject BTC/macro data.")