# Chatbot API Key Integration Guide

## Overview
This guide explains how to properly integrate an external AI API (e.g., OpenAI) with your chatbot while keeping API keys secure.

---

## 1. SETUP: API Key Management (SECURE APPROACH)

### Option A: Environment Variables (RECOMMENDED FOR PRODUCTION)

**Step 1: Create a `.env` file** in your project root:
```
OPENAI_API_KEY=sk-your-actual-key-here
FLASK_SECRET_KEY=your-secret-key
```

**Step 2: Install python-dotenv**
```bash
pip install python-dotenv
```

**Step 3: Update app.py** (add at the very top):
```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Your Flask app setup follows...
```

### Option B: Config File (DEVELOPMENT)

Create a `config.py`:
```python
import os

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-default-key')
    API_PROVIDER = 'openai'  # or 'anthropic', 'gemini', etc.
```

---

## 2. BACKUP: Configuration Methods

| Method | Use Case | Security |
|--------|----------|----------|
| **Environment Variables** | Production, shared servers | ⭐⭐⭐ Best |
| **.env file** | Local development | ⭐⭐ Good |
| **Config file (gitignored)** | Team development | ⭐⭐ Good |
| **Hardcoded** | ❌ NEVER | ⭐ Worst |

---

## 3. IMPLEMENTATION: Backend Changes (app.py)

### Add these imports at the top:
```python
import requests
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

### Replace the `/chatbot_api` endpoint with this improved version:

```python
@app.route('/chatbot_api', methods=['POST'])
def chatbot_api():
    """Enhanced chatbot with external AI API + local fallback."""
    try:
        data = request.get_json() or {}
        msg = (data.get('message') or '').strip()
        
        if not msg:
            return jsonify({'reply': 'Please ask a question about the current lab (commands, hints, or next steps).'})

        # Safety: require a started lab session
        if not session.get('lab_id') or not session.get('lab_name'):
            return jsonify({'reply': 'Please start a lab session first.'})

        # Forbidden/unsafe checks
        forbidden = ['bomb', 'kill', 'terror', 'weapon', 'ddos', 'hack bank', 'attack real']
        low = msg.lower()
        if any(term in low for term in forbidden):
            return jsonify({'reply': 'Sorry — I can only provide safe, lab-specific guidance.'})

        # Try external AI API first (if key is available)
        if OPENAI_API_KEY:
            ai_response = call_openai_api(msg, session.get('lab_name'))
            if ai_response:
                return jsonify({'reply': ai_response})
        
        # Fallback to local database lookup
        return get_local_chatbot_response(msg, session.get('lab_name'))
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'reply': 'Assistant is unavailable right now.'})


def call_openai_api(message, lab_name):
    """Call OpenAI API with error handling."""
    try:
        if not OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not configured")
            return None
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-3.5-turbo',  # or 'gpt-4' for better quality
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are a helpful lab assistant for a {lab_name} lab. Provide concise, relevant guidance about commands and security concepts for this lab. Keep responses under 200 words.'
                    },
                    {
                        'role': 'user',
                        'content': message
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 300,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content'].strip()
            return reply
        else:
            print(f"OpenAI API error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("OpenAI API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"OpenAI API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error calling OpenAI: {e}")
        return None


def get_local_chatbot_response(msg, lab_name):
    """Fallback local database response."""
    try:
        lab_type = get_session_lab_type()
        matches = []
        
        try:
            conn = get_lab_db_connection(lab_type)
            cur = conn.cursor()
            for table in ('attack_commands', 'defense_commands'):
                try:
                    cur.execute(
                        f"SELECT name,pattern,hint,example FROM {table} WHERE name LIKE ? OR pattern LIKE ? OR hint LIKE ? OR example LIKE ? LIMIT 5",
                        tuple(['%'+msg+'%']*4)
                    )
                    rows = cur.fetchall()
                    for r in rows:
                        matches.append({
                            'name': r[0] if isinstance(r, tuple) else r['name'], 
                            'pattern': r[1] if isinstance(r, tuple) else r['pattern'],
                            'hint': (r[2] if isinstance(r, tuple) else r.get('hint')),
                            'example': (r[3] if isinstance(r, tuple) else r.get('example'))
                        })
                except Exception:
                    pass
        except Exception:
            pass

        if matches:
            parts = []
            for m in matches[:3]:
                name = m.get('name') or m.get('pattern')
                hint = m.get('hint') or ''
                ex = m.get('example') or ''
                parts.append(f"**{name}**: {hint}\n```\n{ex}\n```")
            reply = "Here are relevant commands:\n\n" + "\n\n".join(parts)
            return jsonify({'reply': reply})

        guidance = {
            's3': "S3 Bucket lab — start with reconnaissance: 'aws s3 ls', 'aws s3 ls s3://<bucket>'. Use 'aws s3 cp' to simulate downloads. Mitigate with 'aws s3api put-public-access-block'.",
            'pwndora': "PwnDora lab — begin with recon: use 'curl', 'ls', 'cat' to inspect files. Test input fields for injection or XSS. Check the cheatsheet for examples.",
            'network': "Network Recon lab — use 'nmap -sV <target>' for enumeration, then 'traceroute' and targeted probes."
        }

        lab_type_name = lab_type or 's3'
        return jsonify({'reply': guidance.get(lab_type_name, 'Ask about commands or hints for the current lab.')})
        
    except Exception as e:
        print(f"Local response error: {e}")
        return jsonify({'reply': 'Assistant is unavailable right now.'})
```

---

## 4. FRONTEND: Update chatbot.js (error handling)

The frontend is already correct, but here's an improved version with better error messages:

```javascript
(() => {
  const toggle = document.getElementById('chatbot-toggle');
  const win = document.getElementById('chatbot-window');
  const closeBtn = document.getElementById('chatbot-close');
  const form = document.getElementById('chatbot-form');
  const input = document.getElementById('chatbot-input');
  const messages = document.getElementById('chatbot-messages');

  function openWindow(){ 
    win.style.display='flex'; 
    win.setAttribute('aria-hidden','false'); 
    input.focus(); 
  }
  
  function closeWindow(){ 
    win.style.display='none'; 
    win.setAttribute('aria-hidden','true'); 
  }

  toggle && toggle.addEventListener('click', ()=>{
    if(win.style.display==='flex') closeWindow(); else openWindow();
  });
  
  closeBtn && closeBtn.addEventListener('click', closeWindow);

  function appendMessage(text, cls='bot'){
    const el = document.createElement('div'); 
    el.className = cls; 
    el.textContent = text; 
    messages.appendChild(el); 
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage(message){
    appendMessage(message, 'user');
    appendMessage('…', 'bot');
    
    try{
      const res = await fetch('/chatbot_api', { 
        method: 'POST', 
        headers: {'Content-Type':'application/json'}, 
        body: JSON.stringify({message}),
        timeout: 15000  // 15 second timeout
      });
      
      const json = await res.json();
      const lastBot = messages.querySelectorAll('.bot');
      if(lastBot.length) lastBot[lastBot.length-1].remove();
      
      if(res.ok && json && json.reply){
        appendMessage(json.reply, 'bot');
      } else {
        appendMessage('Unable to get a response. Please check the API configuration.', 'bot');
      }
    } catch(err){
      const lastBot = messages.querySelectorAll('.bot');
      if(lastBot.length) lastBot[lastBot.length-1].remove();
      console.error('Chat error:', err);
      appendMessage('Error: Could not reach the assistant. Please try again.', 'bot');
    }
  }

  form && form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const v = input.value && input.value.trim();
    if(!v) return;
    input.value='';
    sendMessage(v);
  });
})();
```

---

## 5. GETTING YOUR API KEY

### For OpenAI:
1. Go to https://platform.openai.com/signup
2. Create an account and verify email
3. Go to "API keys" section
4. Click "Create new secret key"
5. Copy and save it (you won't see it again!)
6. Add to your `.env` file: `OPENAI_API_KEY=sk-...`

### For other providers:
- **Anthropic (Claude)**: https://console.anthropic.com/
- **Google Gemini**: https://ai.google.dev/
- **Azure OpenAI**: https://azure.microsoft.com/

---

## 6. INSTALLATION

```bash
# Install required packages
pip install requests python-dotenv

# For development with OpenAI
pip install openai
```

---

## 7. TESTING YOUR SETUP

### Test 1: Verify API Key is loaded
Create a test file `test_chatbot_setup.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

if api_key:
    print(f"✓ API Key found (length: {len(api_key)})")
    print(f"✓ Starts with: {api_key[:10]}...")
else:
    print("✗ API Key NOT found in environment")
```

Run: `python test_chatbot_setup.py`

### Test 2: Test API Connection
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

response = requests.post(
    'https://api.openai.com/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json',
    },
    json={
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'Say hello'}],
        'max_tokens': 10,
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✓ API Connection successful!")
    print(f"Response: {response.json()['choices'][0]['message']['content']}")
else:
    print(f"✗ Error: {response.text}")
```

---

## 8. COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Check `.env` file, regenerate key |
| `Timeout` | API too slow | Increase timeout, check internet |
| `None` returned | API key not loaded | Verify `.env` and `load_dotenv()` called |
| `CORS error` | Browser policy | Not applicable for backend calls |
| `Module not found: dotenv` | Package not installed | Run `pip install python-dotenv` |

---

## 9. SECURITY BEST PRACTICES

✅ **DO:**
- Store keys in `.env` file (add to `.gitignore`)
- Use environment variables in production
- Rotate keys regularly
- Use specific API permissions/scopes

❌ **DON'T:**
- Commit `.env` to git
- Hardcode keys in source files
- Share API keys in plain text
- Use the same key everywhere

---

## 10. DEPLOYMENT NOTES

### On Heroku:
```bash
heroku config:set OPENAI_API_KEY=sk-your-key
```

### On AWS/Azure:
Use Secrets Manager or Key Vault, then load in app.py:
```python
import json
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='chatbot-api-key')
OPENAI_API_KEY = json.loads(secret['SecretString'])['api_key']
```

---

## 11. NEXT STEPS

1. ✓ Create `.env` file with your API key
2. ✓ Install `python-dotenv` and `requests`
3. ✓ Update `app.py` with the new chatbot functions
4. ✓ Test the setup with provided test scripts
5. ✓ Update `chatbot.js` for better error handling
6. ✓ Restart your Flask app and test the chatbot

---

## Questions?

If you encounter issues:
1. Check console logs: `python app.py` (watch for errors)
2. Check `.env` file exists and has correct format
3. Verify API key is valid and has quota
4. Test API directly with curl or Postman
