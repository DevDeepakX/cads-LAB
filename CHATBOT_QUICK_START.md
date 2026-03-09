# Quick Start Guide: Getting Your Chatbot Running with API Key

## ⚡ 5-Minute Setup

### Step 1: Get Your API Key (2 minutes)
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. **Save it somewhere safe** - you won't see it again!

### Step 2: Create `.env` File (1 minute)
In your project root directory (`d:\Desktop\C_A_D_S\`), create a file named `.env`:

```
OPENAI_API_KEY=sk-your-actual-key-here-replace-this
FLASK_SECRET_KEY=your-secret-key
```

**⚠️ IMPORTANT:** Replace `sk-your-actual-key-here-replace-this` with your real key!

### Step 3: Install Dependencies (1 minute)
Open PowerShell in your project directory and run:

```powershell
pip install requests python-dotenv
```

### Step 4: Test Your Setup (1 minute)
```powershell
python test_chatbot_setup.py
```

You should see mostly ✓ marks. If not, see the Troubleshooting section below.

### Step 5: Run Your App
```powershell
python app.py
```

Then open http://localhost:5000 in your browser.

---

## 🧪 Testing the Chatbot

1. **Start a Lab**: Go to any lab page and click "Start Lab"
2. **Open Chatbot**: Look for the ghost icon in the bottom right
3. **Ask a Question**: Try "How do I list S3 buckets?" or "Tell me about reconnaissance"
4. **Check Response**: Should get an AI-powered answer

---

## 🐛 Troubleshooting

### ✗ "API Key NOT found"
**Problem:** `.env` file not created or API key not set

**Fix:**
1. Create `.env` file in project root (same directory as `app.py`)
2. Add: `OPENAI_API_KEY=sk-your-key-here`
3. Save the file
4. Run `python test_chatbot_setup.py` again

### ✗ "API authentication failed (401 Unauthorized)"
**Problem:** Invalid or expired API key

**Fix:**
1. Go to https://platform.openai.com/api-keys
2. Delete the old key
3. Create a new one
4. Update `.env` with the new key
5. Restart your Flask app

### ✗ "API error: 429"
**Problem:** Rate limit exceeded (too many requests)

**Fix:**
1. Wait a few minutes before making more requests
2. Check your usage at https://platform.openai.com/account/usage/overview
3. Consider using a different model or reducing request frequency

### ✗ "python-dotenv is NOT installed"
**Problem:** Missing package

**Fix:**
```powershell
pip install python-dotenv
```

### ✗ "Connection error"
**Problem:** Network issue or firewall blocking the API

**Fix:**
1. Check your internet connection
2. Try disabling your VPN (if using one)
3. Check firewall settings
4. Try a simple test: `ping api.openai.com`

### ✗ Chatbot not appearing in browser
**Problem:** JavaScript issue or CSS problem

**Fix:**
1. Check browser console (F12 → Console tab)
2. Look for JavaScript errors
3. Check that `/static/chatbot.js` is being loaded
4. Check that `/static/chatbot.css` is being loaded
5. Try clearing browser cache (Ctrl+Shift+Del)

### ✗ "Please start a lab session first"
**Problem:** Chatbot accessed without starting a lab

**Fix:**
1. Go to a lab introduction page (e.g., Open S3 Bucket lab)
2. Click the "Start Lab" button
3. Wait for the lab to load
4. Now try the chatbot

---

## 📝 File Structure After Setup

```
d:\Desktop\C_A_D_S\
├── app.py                                  (Updated with API support)
├── .env                                    (Create this - your API key!)
├── .env.example                            (Template for .env)
├── CHATBOT_API_INTEGRATION_GUIDE.md        (Full documentation)
├── CHATBOT_QUICK_START.md                  (This file)
├── test_chatbot_setup.py                   (Run this to verify setup)
├── test_chatbot_endpoint.py                (Run this to test endpoint)
├── templates/
│   └── _chatbot.html                       (Chatbot UI)
├── static/
│   ├── chatbot.js                          (Already updated)
│   ├── chatbot.css                         (Styles)
│   └── ghost.svg                           (Ghost icon)
└── ... (other files)
```

---

## 🔒 Security Reminder

⚠️ **NEVER commit `.env` to git!**

The `.env` file contains your API key. If you commit it, anyone with access to your repo can use your key and run up charges.

**To prevent accidental commits:**

1. The `.env` file should be in `.gitignore` (if using git)
2. Use `.env.example` to show what variables are needed
3. Team members copy `.env.example` to `.env` and fill in their own keys

---

## 📊 Monitoring Your API Usage

Since you're using an external API, you may incur costs depending on your API plan.

**To check usage:**
1. Go to https://platform.openai.com/account/usage/overview
2. Check how many tokens you've used
3. View your spending limits

**To reduce costs:**
- Use `gpt-3.5-turbo` (cheaper) instead of `gpt-4`
- Reduce `max_tokens` from 300 to 200
- Use the local database fallback for common questions

---

## 🚀 Advanced Options

### Use a Different AI Model
Edit `.env`:
```
OPENAI_MODEL=gpt-4
```

**Models available:**
- `gpt-3.5-turbo` (cheapest, fast)
- `gpt-4` (better quality, more expensive)
- `gpt-4-turbo` (faster than gpt-4)

### Use a Different AI Provider
If you prefer another provider, update `app.py`:
- **Anthropic (Claude)**: Replace OpenAI calls with Anthropic API
- **Google Gemini**: Use Google's API endpoint
- **Local LLaMA**: Run a model locally

### Add Rate Limiting
To prevent abuse, add rate limiting to `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["5 per minute"])

@app.route('/chatbot_api', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 messages per minute
def chatbot_api():
    # ... existing code
```

---

## ❓ Still Have Issues?

1. **Read the full guide**: [CHATBOT_API_INTEGRATION_GUIDE.md](CHATBOT_API_INTEGRATION_GUIDE.md)
2. **Check test output**: Run `python test_chatbot_setup.py` to see detailed diagnostics
3. **Review Flask logs**: Watch the terminal where you ran `python app.py` for errors
4. **Browser console**: Open F12 and check the Console tab for JavaScript errors

---

## ✅ You're Done!

Your chatbot is now configured to use API keys securely and will provide AI-powered responses to lab questions. If you have a configuration error, the chatbot will gracefully fall back to the local database.

**Next, you might want to:**
- [ ] Test the chatbot thoroughly
- [ ] Adjust the system prompt in `app.py` for your use case
- [ ] Set up monitoring for API usage
- [ ] Configure rate limiting for production
- [ ] Deploy to your hosting platform

Happy coding! 🚀
