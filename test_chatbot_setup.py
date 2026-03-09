#!/usr/bin/env python3
"""
Test script to verify chatbot API key configuration and connectivity.
Run this to diagnose any issues with your API setup.
"""

import os
import sys
from pathlib import Path

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_env_loading():
    """Test 1: Verify environment loading."""
    print_section("TEST 1: Environment Loading")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv is installed")
    except ImportError:
        print("✗ python-dotenv NOT installed")
        print("  Fix: Run 'pip install python-dotenv'")
        return False
    
    # Try loading .env
    dotenv_path = Path(__file__).parent / '.env'
    if dotenv_path.exists():
        print(f"✓ .env file found at: {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        print(f"✗ .env file NOT found at: {dotenv_path}")
        print(f"  Expected location: {dotenv_path}")
        print("  Fix: Create .env file from .env.example")
        return False
    
    return True

def test_api_key():
    """Test 2: Verify API key is loaded."""
    print_section("TEST 2: API Key Configuration")
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("✗ OPENAI_API_KEY environment variable is NOT set")
        print("  Fix: Add OPENAI_API_KEY=sk-... to your .env file")
        return False
    
    if len(api_key) < 20:
        print("✗ API key appears to be too short (likely invalid)")
        print(f"  Current length: {len(api_key)} characters")
        return False
    
    print(f"✓ API key is loaded")
    print(f"  Key prefix: {api_key[:10]}...")
    print(f"  Key length: {len(api_key)} characters")
    
    if not api_key.startswith('sk-'):
        print("⚠ Warning: OpenAI keys typically start with 'sk-'")
        print(f"  Your key starts with: '{api_key[:5]}'")
    
    return True

def test_requests_library():
    """Test 3: Verify requests library is installed."""
    print_section("TEST 3: Required Libraries")
    
    try:
        import requests
        print(f"✓ requests library is installed (version {requests.__version__})")
    except ImportError:
        print("✗ requests library NOT installed")
        print("  Fix: Run 'pip install requests'")
        return False
    
    try:
        import flask
        print(f"✓ flask is installed (version {flask.__version__})")
    except ImportError:
        print("✗ flask NOT installed")
        return False
    
    return True

def test_api_connectivity():
    """Test 4: Test actual API connectivity."""
    print_section("TEST 4: API Connectivity")
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("✗ Skipping (API key not configured)")
        return False
    
    try:
        import requests
        
        print("Testing connection to OpenAI API...")
        print("(This may take 10-15 seconds)")
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': 'Say "API connection successful" in exactly 5 words.'}
                ],
                'max_tokens': 20,
                'temperature': 0.7
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print("✓ API connection successful!")
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                msg = data['choices'][0]['message']['content'].strip()
                print(f"  Response: \"{msg}\"")
                return True
        elif response.status_code == 401:
            print("✗ API authentication failed (401 Unauthorized)")
            print("  Reasons:")
            print("    - API key is invalid or expired")
            print("    - API key has wrong format")
            print("  Fix: Generate a new key from https://platform.openai.com/api-keys")
            return False
        elif response.status_code == 429:
            print("✗ Rate limit exceeded (429)")
            print("  Your account or API key has exceeded its rate limit")
            print("  Fix: Wait a moment or check your usage at platform.openai.com")
            return False
        else:
            print(f"✗ API error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ API request timed out (took longer than 15 seconds)")
        print("  Possible causes:")
        print("    - API server is slow")
        print("    - Network connectivity issue")
        print("  Fix: Check your internet connection and try again")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {str(e)}")
        print("  Possible causes:")
        print("    - Network connectivity issue")
        print("    - Firewall blocking the connection")
        print("    - API endpoint is unreachable")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

def test_app_imports():
    """Test 5: Verify Flask app can import properly."""
    print_section("TEST 5: Flask App Imports")
    
    try:
        # Try to import the app (might fail if there are import issues)
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Check if app.py exists
        app_path = Path(__file__).parent / 'app.py'
        if not app_path.exists():
            print(f"✗ app.py not found at {app_path}")
            return False
        
        print(f"✓ app.py found at {app_path}")
        
        # Try importing (might fail due to database issues, which is OK)
        try:
            from app import app, OPENAI_API_KEY, OPENAI_MODEL
            print("✓ Successfully imported Flask app")
            print(f"  OPENAI_API_KEY configured: {bool(OPENAI_API_KEY)}")
            print(f"  OPENAI_MODEL: {OPENAI_MODEL}")
            return True
        except Exception as e:
            print(f"⚠ Warning importing app: {str(e)}")
            print("  This might be OK if it's a database connection issue")
            print("  Check that your Flask dependencies are installed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def print_summary(results):
    """Print test results summary."""
    print_section("TEST SUMMARY")
    
    tests = [
        ("Environment Loading", results[0]),
        ("API Key Configuration", results[1]),
        ("Required Libraries", results[2]),
        ("API Connectivity", results[3]),
        ("Flask App Imports", results[4])
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Your chatbot is ready to use.")
        print("\nNext steps:")
        print("  1. Start your Flask app: python app.py")
        print("  2. Open http://localhost:5000 in your browser")
        print("  3. Start a lab and test the chatbot")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed. See above for fixes.")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  CHATBOT API CONFIGURATION TEST")
    print("="*60)
    
    results = [
        test_env_loading(),
        test_api_key(),
        test_requests_library(),
        test_api_connectivity(),
        test_app_imports(),
    ]
    
    success = print_summary(results)
    
    print("\n" + "="*60)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
