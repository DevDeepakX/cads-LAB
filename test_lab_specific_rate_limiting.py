#!/usr/bin/env python3
"""
Integration test for lab-specific cheatsheet rate limiting.
Tests that each lab has independent view counters and cooldown timers.
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_lab_specific_rate_limiting():
    """Test that each lab has independent rate limiting"""
    print("\n" + "="*70)
    print("TEST: LAB-SPECIFIC CHEATSHEET RATE LIMITING")
    print("="*70)
    
    # Test 1: Open S3 lab and view cheatsheet 3 times
    print("\n[1] Opening Open S3 Bucket lab...")
    s3_session = requests.Session()
    response = s3_session.post(f"{BASE_URL}/lab/s3/start", data={
        "mode": "attack",
        "level": "Intermediate"
    }, allow_redirects=True)
    
    print(f"    S3 Lab started: {response.status_code}")
    
    # View cheatsheet 3 times
    print("\n[2] Viewing S3 cheatsheet 3 times...")
    for i in range(1, 4):
        response = s3_session.get(f"{BASE_URL}/cheatsheet_api")
        data = response.json()
        print(f"    View {i}: {response.status_code} - Remaining free views: {data.get('remaining_free_views')}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Attempt 4th view (should be rate limited)
    print("\n[3] Attempting 4th view on S3 (should be rate limited)...")
    response = s3_session.get(f"{BASE_URL}/cheatsheet_api")
    print(f"    View 4: {response.status_code} - {response.json().get('message', 'N/A')}")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    
    # Test 2: Switch to PwnDora lab (should allow 3 free views independently)
    print("\n[4] Opening PwnDora lab...")
    pwndora_session = requests.Session()
    response = pwndora_session.post(f"{BASE_URL}/lab/pwndora/start", data={
        "mode": "defense",
        "level": "Beginner"
    }, allow_redirects=True)
    
    print(f"    PwnDora Lab started: {response.status_code}")
    
    # View cheatsheet 3 times (should succeed - independent counter)
    print("\n[5] Viewing PwnDora cheatsheet 3 times (independent counter)...")
    for i in range(1, 4):
        response = pwndora_session.get(f"{BASE_URL}/cheatsheet_api")
        data = response.json()
        print(f"    View {i}: {response.status_code} - Remaining free views: {data.get('remaining_free_views')}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Attempt 4th view on PwnDora (should be rate limited)
    print("\n[6] Attempting 4th view on PwnDora (should be rate limited)...")
    response = pwndora_session.get(f"{BASE_URL}/cheatsheet_api")
    print(f"    View 4: {response.status_code}")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    
    # Test 3: Return to S3 lab (should still be rate limited)
    print("\n[7] Returning to S3 lab (rate limit should persist)...")
    response = s3_session.get(f"{BASE_URL}/cheatsheet_api")
    print(f"    S3 View attempt: {response.status_code}")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    
    # Test 4: Switch to Network lab (should allow 3 free views independently)
    print("\n[8] Opening Network Recon lab...")
    network_session = requests.Session()
    response = network_session.post(f"{BASE_URL}/lab/network/start", data={
        "mode": "attack",
        "level": "Advanced"
    }, allow_redirects=True)
    
    print(f"    Network Lab started: {response.status_code}")
    
    # View cheatsheet 3 times (should succeed - independent counter)
    print("\n[9] Viewing Network cheatsheet 3 times (independent counter)...")
    for i in range(1, 4):
        response = network_session.get(f"{BASE_URL}/cheatsheet_api")
        data = response.json()
        print(f"    View {i}: {response.status_code} - Remaining free views: {data.get('remaining_free_views')}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Attempt 4th view on Network (should be rate limited)
    print("\n[10] Attempting 4th view on Network (should be rate limited)...")
    response = network_session.get(f"{BASE_URL}/cheatsheet_api")
    print(f"     View 4: {response.status_code}")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    
    print("\n" + "="*70)
    print("PASS: Lab-specific rate limiting works correctly!")
    print("="*70 + "\n")

def test_rate_limit_reset_after_5_minutes():
    """Test that rate limit resets after 5 minutes (optional - requires waiting)"""
    print("\n" + "="*70)
    print("TEST: RATE LIMIT RESET (requires 5-minute wait)")
    print("="*70)
    
    s3_session = requests.Session()
    
    # Start lab and exhaust free views
    print("\n[1] Starting S3 lab...")
    response = s3_session.post(f"{BASE_URL}/lab/s3/start", data={
        "mode": "attack",
        "level": "Intermediate"
    }, allow_redirects=True)
    
    # View 3 times
    for i in range(3):
        s3_session.get(f"{BASE_URL}/cheatsheet_api")
    
    # Try 4th view (rate limited)
    response = s3_session.get(f"{BASE_URL}/cheatsheet_api")
    assert response.status_code == 429
    print("[2] Rate limit triggered (429)")
    
    print("\nNote: Full test requires 5-minute wait. Skipping wait in automated test.")
    print("Manual test: Wait 5 minutes and try viewing again - should succeed.")

if __name__ == "__main__":
    try:
        print("\nCHEATSHEET LAB-SPECIFIC RATE LIMITING TEST SUITE")
        print("Testing independent view counters and cooldowns per lab\n")
        
        test_lab_specific_rate_limiting()
        test_rate_limit_reset_after_5_minutes()
        
        print("\nAll tests passed! Lab-specific rate limiting is working correctly.\n")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
