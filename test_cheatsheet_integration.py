#!/usr/bin/env python3
"""
Integration test for mode-based cheatsheet filtering.
Tests the complete flow from lab start to cheatsheet API calls.
"""

import requests
import json
from http.cookiejar import CookieJar

BASE_URL = "http://127.0.0.1:5000"

def test_s3_attack_mode():
    """Test S3 lab with Attack mode"""
    print("\n" + "="*60)
    print("TEST 1: S3 Lab - Attack Mode")
    print("="*60)
    
    session = requests.Session()
    
    # Step 1: Start the S3 lab with Attack mode
    response = session.post(f"{BASE_URL}/lab/s3/start", data={
        "mode": "attack",
        "level": "Intermediate"
    }, allow_redirects=False)
    
    print(f"Lab start response: {response.status_code}")
    
    # Step 2: Fetch cheatsheet API
    response = session.get(f"{BASE_URL}/cheatsheet_api")
    if response.status_code == 200:
        data = response.json()
        commands = data.get('commands', [])
        mode = data.get('mode', 'unknown')
        
        print(f"Mode: {mode}")
        print(f"Total commands returned: {len(commands)}")
        
        if commands:
            print("\nFirst 3 commands:")
            for i, cmd in enumerate(commands[:3], 1):
                print(f"  {i}. {cmd.get('name')} - {cmd.get('description')}")
        
        # Verify mode filtering
        if mode == "attack":
            print("✅PASS: Attack mode returned successfully")
        else:
            print(f"❌FAIL: Expected attack mode, got {mode}")
    else:
        print(f"❌FAIL: Cheatsheet API returned {response.status_code}")
        print(response.text)

def test_s3_defense_mode():
    """Test S3 lab with Defense mode"""
    print("\n" + "="*60)
    print("TEST 2: S3 Lab - Defense Mode")
    print("="*60)
    
    session = requests.Session()
    
    # Step 1: Start the S3 lab with Defense mode
    response = session.post(f"{BASE_URL}/lab/s3/start", data={
        "mode": "defense",
        "level": "Intermediate"
    }, allow_redirects=False)
    
    print(f"Lab start response: {response.status_code}")
    
    # Step 2: Fetch cheatsheet API
    response = session.get(f"{BASE_URL}/cheatsheet_api")
    if response.status_code == 200:
        data = response.json()
        commands = data.get('commands', [])
        mode = data.get('mode', 'unknown')
        
        print(f"Mode: {mode}")
        print(f"Total commands returned: {len(commands)}")
        
        if commands:
            print("\nFirst 3 commands:")
            for i, cmd in enumerate(commands[:3], 1):
                print(f"  {i}. {cmd.get('name')} - {cmd.get('description')}")
        
        # Verify mode filtering
        if mode == "defense":
            print("✅PASS: Defense mode returned successfully")
        else:
            print(f"❌FAIL: Expected defense mode, got {mode}")
    else:
        print(f"❌FAIL: Cheatsheet API returned {response.status_code}")
        print(response.text)

def test_pwndora_attack_mode():
    """Test PwnDora lab with Attack mode"""
    print("\n" + "="*60)
    print("TEST 3: PwnDora Lab - Attack Mode")
    print("="*60)
    
    session = requests.Session()
    
    # Step 1: Start the PwnDora lab with Attack mode
    response = session.post(f"{BASE_URL}/lab/pwndora/start", data={
        "mode": "attack",
        "level": "Beginner"
    }, allow_redirects=False)
    
    print(f"Lab start response: {response.status_code}")
    
    # Step 2: Fetch cheatsheet API
    response = session.get(f"{BASE_URL}/cheatsheet_api")
    if response.status_code == 200:
        data = response.json()
        commands = data.get('commands', [])
        mode = data.get('mode', 'unknown')
        
        print(f"Mode: {mode}")
        print(f"Total commands returned: {len(commands)}")
        
        if commands:
            print("\nFirst 3 commands:")
            for i, cmd in enumerate(commands[:3], 1):
                print(f"  {i}. {cmd.get('name')} - {cmd.get('description')}")
        
        # Verify mode filtering
        if mode == "attack":
            print("✅PASS: Attack mode returned successfully")
        else:
            print(f"❌FAIL: Expected attack mode, got {mode}")
    else:
        print(f"❌FAIL: Cheatsheet API returned {response.status_code}")
        print(response.text)

def test_network_defense_mode():
    """Test Network Recon lab with Defense mode"""
    print("\n" + "="*60)
    print("TEST 4: Network Recon Lab - Defense Mode")
    print("="*60)
    
    session = requests.Session()
    
    # Step 1: Start the Network lab with Defense mode
    response = session.post(f"{BASE_URL}/lab/network/start", data={
        "mode": "defense",
        "level": "Advanced"
    }, allow_redirects=False)
    
    print(f"Lab start response: {response.status_code}")
    
    # Step 2: Fetch cheatsheet API
    response = session.get(f"{BASE_URL}/cheatsheet_api")
    if response.status_code == 200:
        data = response.json()
        commands = data.get('commands', [])
        mode = data.get('mode', 'unknown')
        
        print(f"Mode: {mode}")
        print(f"Total commands returned: {len(commands)}")
        
        if commands:
            print("\nFirst 3 commands:")
            for i, cmd in enumerate(commands[:3], 1):
                print(f"  {i}. {cmd.get('name')} - {cmd.get('description')}")
        
        # Verify mode filtering
        if mode == "defense":
            print("✅PASS: Defense mode returned successfully")
        else:
            print(f"❌FAIL: Expected defense mode, got {mode}")
    else:
        print(f"❌FAIL: Cheatsheet API returned {response.status_code}")
        print(response.text)

def test_session_initialization():
    """Test that session variables are initialized correctly"""
    print("\n" + "="*60)
    print("TEST 5: Session Initialization Verification")
    print("="*60)
    
    session = requests.Session()
    
    # Start S3 lab
    response = session.post(f"{BASE_URL}/lab/s3/start", data={
        "mode": "attack",
        "level": "Intermediate"
    }, allow_redirects=True)
    
    print(f"Lab start response: {response.status_code}")
    
    # Check if session cookie is set
    cookies = session.cookies.get_dict()
    if 'session' in cookies:
        print("✅PASS: Session cookie set")
    else:
        print("❌FAIL: Session cookie not set")
    
    # Try to fetch terminal page to verify session is active
    response = session.get(f"{BASE_URL}/terminal")
    if response.status_code == 200:
        print("✅PASS: Terminal page loaded successfully (session verified)")
    else:
        print(f"❌FAIL: Terminal page returned {response.status_code}")

if __name__ == "__main__":
    print("\nCHEATSHEET INTEGRATION TEST SUITE")
    print("Testing mode-based filtering and session initialization\n")
    
    try:
        test_s3_attack_mode()
        test_s3_defense_mode()
        test_pwndora_attack_mode()
        test_network_defense_mode()
        test_session_initialization()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
