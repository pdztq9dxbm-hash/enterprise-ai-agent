#!/usr/bin/env python3
"""
Test script to verify OpenAI API setup
Run: python test_openai.py
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_api_key():
    """Test if API key is configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        print("\nPlease add your API key to .env:")
        print("OPENAI_API_KEY=sk-...")
        return False
    
    if api_key == "your_openai_api_key_here":
        print("❌ Please replace the placeholder API key with your actual key")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  Warning: OpenAI API keys typically start with 'sk-'")
    
    print(f"✓ API key found: {api_key[:10]}...{api_key[-5:]}")
    return api_key

def test_connection(api_key):
    """Test basic connection to OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        print("✓ OpenAI client initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return None

def test_model_list(client):
    """List available models"""
    try:
        print("\n📋 Available models:")
        models = client.models.list()
        
        # Filter for chat models
        chat_models = [m for m in models.data if 'gpt' in m.id.lower()]
        for model in chat_models[:10]:  # Show first 10
            print(f"  - {model.id}")
        
        if len(chat_models) > 10:
            print(f"  ... and {len(chat_models) - 10} more")
        
        return True
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return False

def test_simple_generation(client):
    """Test simple text generation"""
    try:
        print("\n🤖 Testing text generation...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✓ Response received: {result}")
        
        # Check token usage
        usage = response.usage
        print(f"  Tokens used: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        return True
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

def test_conversation(client):
    """Test multi-turn conversation"""
    try:
        print("\n💬 Testing conversation...")
        
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        # First message
        response1 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50
        )
        
        answer1 = response1.choices[0].message.content
        print(f"  Q: What is 2+2?")
        print(f"  A: {answer1}")
        
        # Add to conversation
        messages.append({"role": "assistant", "content": answer1})
        messages.append({"role": "user", "content": "Now multiply that by 3"})
        
        # Follow-up
        response2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50
        )
        
        answer2 = response2.choices[0].message.content
        print(f"  Q: Now multiply that by 3")
        print(f"  A: {answer2}")
        
        print("✓ Conversation test passed")
        return True
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

def test_json_mode(client):
    """Test JSON mode for structured output"""
    try:
        print("\n📊 Testing JSON mode...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": 'Create a JSON with keys "name" and "age". Name is "Alice", age is 30.'}
            ],
            response_format={"type": "json_object"},
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        print(f"✓ JSON response: {result}")
        
        import json
        parsed = json.loads(result)
        print(f"  Parsed successfully: {parsed}")
        
        return True
    except Exception as e:
        print(f"❌ JSON mode test failed: {e}")
        return False

def test_streaming(client):
    """Test streaming responses"""
    try:
        print("\n🌊 Testing streaming...")
        
        print("  Response: ", end='', flush=True)
        
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Count from 1 to 5"}
            ],
            stream=True,
            max_tokens=50
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end='', flush=True)
        
        print("\n✓ Streaming test passed")
        return True
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

def test_orchestrator_integration():
    """Test orchestrator integration"""
    try:
        print("\n🎯 Testing Orchestrator integration...")
        from orchestrator.orchestrator import Orchestrator
        
        api_key = os.getenv("OPENAI_API_KEY")
        orchestrator = Orchestrator(api_key=api_key)
        
        print("✓ Orchestrator initialized successfully")
        print(f"  Model: {orchestrator.model}")
        print(f"  Available actions: {len(orchestrator.available_actions)}")
        print(f"  Actions: {', '.join(orchestrator.available_actions.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        print("\nMake sure you're running from the backend directory:")
        print("cd backend && python test_openai.py")
        return False

def main():
    print("=" * 50)
    print("🧪 OpenAI API Test Suite")
    print("=" * 50)
    
    # Test API key first
    api_key = test_api_key()
    if not api_key:
        return 1
    
    # Initialize client
    client = test_connection(api_key)
    if not client:
        return 1
    
    tests = [
        ("Model Listing", lambda: test_model_list(client)),
        ("Simple Generation", lambda: test_simple_generation(client)),
        ("Conversation", lambda: test_conversation(client)),
        ("JSON Mode", lambda: test_json_mode(client)),
        ("Streaming", lambda: test_streaming(client)),
        ("Orchestrator Integration", test_orchestrator_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 50}")
        print(f"Testing: {test_name}")
        print('=' * 50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your OpenAI setup is ready.")
        print("\nRecommended models:")
        print("  - gpt-4o: Most capable, best for complex tasks")
        print("  - gpt-4-turbo: Fast and capable, good balance")
        print("  - gpt-3.5-turbo: Fast and cost-effective")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())