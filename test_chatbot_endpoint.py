#!/usr/bin/env python3
"""
Test script to verify the chatbot endpoint works correctly.
This tests the actual /chatbot_api endpoint response.
"""

import json
import sys
from pathlib import Path

def test_local_chatbot_response():
    """Test the local database fallback response."""
    print("\n" + "="*60)
    print("  TESTING LOCAL CHATBOT RESPONSE")
    print("="*60 + "\n")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app import get_local_chatbot_response, app
        
        # Create a test app context (Flask requires this for session handling)
        with app.test_request_context():
            from flask import session
            
            # Simulate a lab session
            session['lab_id'] = 'test-lab-123'
            session['lab_name'] = 's3'
            
            # Test queries
            test_queries = [
                "aws s3 command",
                "help with reconnaissance",
                "how to list buckets",
                "What is S3?",
            ]
            
            print("Testing local (database) responses:\n")
            
            for query in test_queries:
                print(f"Query: \"{query}\"")
                response = get_local_chatbot_response(query, 's3')
                data = response.get_json()
                print(f"Response: {data.get('reply', 'No reply')}\n")
                print("-" * 60 + "\n")
            
            print("✓ Local chatbot response test completed")
            return True
            
    except Exception as e:
        print(f"✗ Error testing local response: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_api_call():
    """Test direct OpenAI API call."""
    print("\n" + "="*60)
    print("  TESTING OPENAI API CALL")
    print("="*60 + "\n")
    
    import os
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("✗ OPENAI_API_KEY not set in environment")
        print("  Skipping OpenAI test")
        return None
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app import call_openai_api, app
        
        with app.test_request_context():
            print("Testing OpenAI API call...\n")
            
            test_queries = [
                "What is AWS S3?",
                "How do I list S3 buckets?",
            ]
            
            for query in test_queries:
                print(f"Query: \"{query}\"")
                response = call_openai_api(query, 's3')
                
                if response:
                    print(f"✓ Response: {response[:150]}...")
                else:
                    print(f"✗ No response from API")
                
                print("-" * 60 + "\n")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing OpenAI API: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_full_endpoint():
    """Test the full /chatbot_api endpoint."""
    print("\n" + "="*60)
    print("  TESTING FULL CHATBOT ENDPOINT")
    print("="*60 + "\n")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app import app
        
        with app.test_client() as client:
            print("Testing chatbot API endpoint...\n")
            
            # Test 1: Without session (should fail)
            print("Test 1: Request without lab session")
            response = client.post(
                '/chatbot_api',
                json={'message': 'test'},
                content_type='application/json'
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.get_json()}")
            print()
            
            # Test 2: With session
            print("Test 2: Request with lab session")
            with client.session_transaction() as sess:
                sess['lab_id'] = 'test-123'
                sess['lab_name'] = 's3'
            
            response = client.post(
                '/chatbot_api',
                json={'message': 'How do I list buckets?'},
                content_type='application/json'
            )
            print(f"  Status: {response.status_code}")
            data = response.get_json()
            print(f"  Response: {data.get('reply', 'No reply')[:200]}...")
            print()
            
            # Test 3: Unsafe query
            print("Test 3: Unsafe query (should be blocked)")
            response = client.post(
                '/chatbot_api',
                json={'message': 'how to ddos a server'},
                content_type='application/json'
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.get_json()}")
            print()
            
            print("✓ Full endpoint test completed")
            return True
            
    except Exception as e:
        print(f"✗ Error testing endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all chatbot tests."""
    print("\n" + "="*60)
    print("  CHATBOT ENDPOINT TESTS")
    print("="*60)
    
    print("\nMake sure your Flask app's dependencies are installed:")
    print("  - Flask")
    print("  - requests")
    print("  - python-dotenv")
    
    results = []
    
    results.append(test_local_chatbot_response())
    results.append(test_openai_api_call())
    results.append(test_full_endpoint())
    
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"\nResults:")
    print(f"  ✓ Passed: {passed}")
    print(f"  ✗ Failed: {failed}")
    print(f"  ⊘ Skipped: {skipped}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
