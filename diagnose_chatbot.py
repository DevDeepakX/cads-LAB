#!/usr/bin/env python3
"""
Chatbot Diagnostic Tool
Comprehensive troubleshooting and environment report
"""

import os
import sys
from pathlib import Path

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title:^66}")
    print(f"{'='*70}\n")

def print_section(title):
    print(f"\n{title}")
    print(f"{'-'*70}\n")

def get_system_info():
    """Get system and Python information."""
    print_section("SYSTEM INFORMATION")
    
    print(f"Python Version:        {sys.version}")
    print(f"Python Executable:     {sys.executable}")
    print(f"Platform:              {sys.platform}")
    print(f"Working Directory:     {os.getcwd()}")
    print(f"Project Root:          {Path(__file__).parent}")

def check_required_files():
    """Check for required files."""
    print_section("REQUIRED FILES")
    
    project_root = Path(__file__).parent
    required_files = {
        'app.py': 'Main Flask application',
        '.env': 'Environment configuration (CREATE THIS)',
        '.env.example': 'Environment template',
        'requirements.txt': 'Python dependencies',
        'templates/_chatbot.html': 'Chatbot HTML template',
        'static/chatbot.js': 'Chatbot JavaScript',
        'static/chatbot.css': 'Chatbot styles',
    }
    
    for filename, description in required_files.items():
        file_path = project_root / filename
        exists = "✓" if file_path.exists() else "✗"
        size = f"({file_path.stat().st_size} bytes)" if file_path.exists() else "(missing)"
        print(f"{exists} {filename:30} | {description:30} {size}")

def check_environment_variables():
    """Check environment variables."""
    print_section("ENVIRONMENT VARIABLES")
    
    variables = {
        'OPENAI_API_KEY': 'API Key for OpenAI',
        'FLASK_SECRET_KEY': 'Flask session secret key',
        'OPENAI_MODEL': 'Model to use (default: gpt-3.5-turbo)',
        'PYTHONPATH': 'Python path',
        'VIRTUAL_ENV': 'Virtual environment path',
    }
    
    for var_name, description in variables.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if 'KEY' in var_name and len(value) > 20:
                display = f"{value[:10]}...{value[-5:]}"
            else:
                display = value
            print(f"✓ {var_name:20} | {description:25} | {display}")
        else:
            print(f"✗ {var_name:20} | {description:25} | NOT SET")

def check_python_packages():
    """Check installed Python packages."""
    print_section("PYTHON PACKAGES")
    
    required_packages = {
        'flask': 'Web framework',
        'requests': 'HTTP client for API calls',
        'dotenv': 'Environment variable loader',
        'sqlite3': 'Database (built-in)',
    }
    
    for package_name, description in required_packages.items():
        try:
            if package_name == 'sqlite3':
                import sqlite3
                version = sqlite3.version
            elif package_name == 'dotenv':
                import dotenv
                version = getattr(dotenv, '__version__', 'unknown')
            else:
                module = __import__(package_name)
                version = getattr(module, '__version__', 'unknown')
            
            print(f"✓ {package_name:15} | {description:30} | version {version}")
        except ImportError:
            print(f"✗ {package_name:15} | {description:30} | NOT INSTALLED")

def check_env_file():
    """Check .env file configuration."""
    print_section("ENVIRONMENT FILE (.env)")
    
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print("✗ .env file NOT FOUND")
        print(f"  Create it at: {env_path}")
        print("\n  Content should include:")
        print("    OPENAI_API_KEY=sk-your-key-here")
        print("    FLASK_SECRET_KEY=your-secret-key")
        return False
    
    print(f"✓ .env file found at: {env_path}")
    
    # Read and validate content
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
        
        print(f"\n  Configuration lines found: {len(lines)}")
        
        has_api_key = False
        for line in lines:
            if line.startswith('OPENAI_API_KEY'):
                has_api_key = True
                if '=' in line:
                    key_part = line.split('=')[1].strip()
                    if key_part and key_part != 'sk-your-actual-api-key-here-replace-this':
                        print(f"  ✓ OPENAI_API_KEY configured (length: {len(key_part)})")
                    else:
                        print(f"  ✗ OPENAI_API_KEY not set or placeholder")
        
        if not has_api_key:
            print(f"  ✗ OPENAI_API_KEY not found in .env")
        
        return has_api_key
        
    except Exception as e:
        print(f"✗ Error reading .env: {str(e)}")
        return False

def check_flask_app():
    """Check Flask app can be imported."""
    print_section("FLASK APPLICATION")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        app_path = Path(__file__).parent / 'app.py'
        if not app_path.exists():
            print(f"✗ app.py not found at {app_path}")
            return False
        
        print(f"✓ app.py found at {app_path}")
        
        # Try to import
        try:
            from app import app, OPENAI_API_KEY, OPENAI_MODEL
            print(f"✓ Flask app imported successfully")
            print(f"  - API Key configured: {bool(OPENAI_API_KEY)}")
            print(f"  - Model: {OPENAI_MODEL}")
            
            # Check routes
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            if '/chatbot_api' in routes:
                print(f"  ✓ /chatbot_api route found")
            else:
                print(f"  ✗ /chatbot_api route NOT found")
            
            return True
            
        except SyntaxError as e:
            print(f"✗ Syntax error in app.py: {str(e)}")
            return False
        except ImportError as e:
            print(f"⚠ Import error (might be OK): {str(e)}")
            return False
        except Exception as e:
            print(f"✗ Error importing app: {str(e)}")
            return False
            
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

def check_api_connectivity():
    """Check OpenAI API connectivity."""
    print_section("API CONNECTIVITY TEST")
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("⊘ Skipping (API key not configured)")
        return None
    
    try:
        import requests
        
        print("Attempting connection to OpenAI API...")
        print("(This may take 10-15 seconds...)\n")
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'user', 'content': 'Say "test" in 1 word.'}
                ],
                'max_tokens': 5,
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print("✓ OpenAI API Connection successful!")
            data = response.json()
            if 'choices' in data:
                msg = data['choices'][0]['message']['content'].strip()
                print(f"  Response: \"{msg}\"")
            return True
        else:
            print(f"✗ API error: {response.status_code}")
            try:
                error = response.json().get('error', {})
                print(f"  Error message: {error.get('message', 'Unknown')}")
            except:
                print(f"  Response: {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Connection timeout (>15 seconds)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

def generate_report():
    """Generate full diagnostic report."""
    print_header("CHATBOT DIAGNOSTIC REPORT")
    
    results = {
        'system': True,
        'files': False,
        'env_vars': False,
        'packages': False,
        'env_file': False,
        'flask_app': False,
        'api_connection': None,
    }
    
    get_system_info()
    check_required_files()
    check_environment_variables()
    check_python_packages()
    results['env_file'] = check_env_file()
    results['flask_app'] = check_flask_app()
    results['api_connection'] = check_api_connectivity()
    
    # Summary
    print_section("SUMMARY & RECOMMENDATIONS")
    
    if results['env_file'] and results['packages'] and results['flask_app']:
        print("✓ Basic setup looks good!")
        
        if results['api_connection'] is True:
            print("✓ API connection successful!")
            print("\n✓✓✓ Everything is configured correctly! ✓✓✓")
            print("\nYou can now:")
            print("  1. Run: python app.py")
            print("  2. Open: http://localhost:5000")
            print("  3. Start a lab and test the chatbot")
        elif results['api_connection'] is False:
            print("✗ API connection failed")
            print("\nTroubleshooting:")
            print("  1. Verify API key at https://platform.openai.com/api-keys")
            print("  2. Check internet connectivity")
            print("  3. Verify firewall settings")
        else:
            print("⊘ API test skipped (API key not configured)")
            print("\nNext steps:")
            print("  1. Create .env file with OPENAI_API_KEY")
            print("  2. Run this diagnostic again")
    else:
        print("✗ Setup incomplete. Issues found:")
        
        if not results['packages']:
            print("  - Missing Python packages")
            print("    Fix: pip install -r requirements.txt")
        
        if not results['env_file']:
            print("  - .env file not configured")
            print("    Fix: Create .env with OPENAI_API_KEY")
        
        if not results['flask_app']:
            print("  - Flask app has issues")
            print("    Fix: Check app.py imports and syntax")
    
    print("\n" + "="*70)
    print("End of diagnostic report")
    print("="*70 + "\n")

if __name__ == '__main__':
    generate_report()
