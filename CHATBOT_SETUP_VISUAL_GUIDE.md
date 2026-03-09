# Chatbot API Integration - Step-by-Step Visual Guide

## 🎯 Goal
Integrate your chatbot with OpenAI's API while keeping your API key secure.

---

## STEP 1️⃣: Get Your OpenAI API Key

```
1. Open https://platform.openai.com/signup
   ├─ Email: your-email@example.com
   ├─ Password: (create strong password)
   └─ Verify email

2. Go to https://platform.openai.com/api-keys
   ├─ Click "Create new secret key"
   ├─ ⚠️ Copy immediately (won't show again!)
   └─ Store in safe place

Your key looks like: sk-proj-abc123def456...
```

**✓ ACTION:** Copy your API key and save somewhere safe

---

## STEP 2️⃣: Create .env File

Navigate to your project folder: `d:\Desktop\C_A_D_S\`

### Using Windows Explorer
```
Right-click in folder
→ New → Text Document
→ Name it: .env.txt
→ Remove .txt extension (so it's just .env)
→ Right-click → Open with → Notepad
```

### Using PowerShell
```powershell
cd d:\Desktop\C_A_D_S
New-Item -Name ".env" -ItemType "File"
notepad .env
```

### File Content
```
OPENAI_API_KEY=sk-... (PASTE YOUR KEY HERE)
FLASK_SECRET_KEY=my-secret-key-12345
```

**Example:**
```
OPENAI_API_KEY=sk-proj-abc123def456ghijk789
FLASK_SECRET_KEY=super-secret-key-xyz789
```

**✓ ACTION:** Create .env file with your API key

---

## STEP 3️⃣: Install Python Packages

Open PowerShell in your project:

```powershell
# Navigate to your project
cd d:\Desktop\C_A_D_S

# Install required packages
pip install -r requirements.txt

# This should install:
# ✓ Flask
# ✓ requests
# ✓ python-dotenv
```

**Expected output:**
```
Successfully installed Flask-3.0.0 requests-2.31.0 python-dotenv-1.0.0
```

**✓ ACTION:** Wait for installation to complete

---

## STEP 4️⃣: Verify Setup

```powershell
# Run diagnostic
python diagnose_chatbot.py

# Or detailed setup test
python test_chatbot_setup.py
```

**Expected output:**
```
✓ Environment Loading
✓ API Key Configuration
✓ Required Libraries
✓ API Connectivity
✓ Flask App Imports

5/5 tests passed!
```

**✓ ACTION:** Check that all tests pass

---

## STEP 5️⃣: Start Your App

```powershell
# Start Flask development server
python app.py

# You should see:
# WARNING: This is a development server. Do not use it in production.
# Running on http://127.0.0.1:5000
# Press CTRL+C to quit
```

**✓ ACTION:** Leave this terminal running

---

## STEP 6️⃣: Test in Browser

```
1. Open http://localhost:5000 in your browser

2. Find a lab (e.g., "Open S3 Bucket Lab")

3. Click "Start Lab"

4. Wait for lab to load
   └─ You should see a ghost icon (👻) in bottom right

5. Click the ghost icon
   └─ Chat window opens

6. Ask a question:
   "How do I list S3 buckets?"

7. Check the response
   ├─ If using API: AI-powered response ✓
   └─ If API fails: Local database response ✓
```

**✓ ACTION:** Test the chatbot with a question

---

## 🔍 Troubleshooting Guide

### Problem: .env file not found
```
❌ Error: OPENAI_API_KEY not configured

✅ Solution:
   1. Check file exists: dir .env
   2. Check format: type .env
   3. Ensure it's named ".env" (not ".env.txt")
```

### Problem: API Key Invalid
```
❌ Error: API authentication failed (401 Unauthorized)

✅ Solution:
   1. Get new key: https://platform.openai.com/api-keys
   2. Delete old key
   3. Create new key
   4. Update .env file
   5. Restart app.py
```

### Problem: Python packages not installed
```
❌ Error: ModuleNotFoundError: No module named 'dotenv'

✅ Solution:
   pip install python-dotenv requests
```

### Problem: Chatbot doesn't appear
```
❌ Ghost icon not visible

✅ Solution:
   1. Press F12 (browser developer tools)
   2. Check Console tab for errors
   3. Check Network tab for 404 errors
   4. Hard refresh: Ctrl+Shift+R
```

### Problem: App won't start
```
❌ Error when running python app.py

✅ Solution:
   python -m flask run --debug
```

---

## 📁 File Structure After Setup

```
d:\Desktop\C_A_D_S\
│
├─ app.py                              ✓ Updated with API support
├─ .env                                ✓ Created (YOUR API KEY HERE)
├─ requirements.txt                    ✓ Dependencies listed
│
├─ templates/
│  └─ _chatbot.html                    ✓ Chatbot UI
│
├─ static/
│  ├─ chatbot.js                       ✓ Already working
│  ├─ chatbot.css                      ✓ Styles
│  └─ ghost.svg                        ✓ Icon
│
├─ Documentation files:
│  ├─ CHATBOT_QUICK_START.md           📖 5-min guide
│  ├─ CHATBOT_API_INTEGRATION_GUIDE.md  📖 Complete reference
│  ├─ CHATBOT_IMPLEMENTATION_SUMMARY.md 📖 Overview
│  └─ CHATBOT_SETUP_VISUAL_GUIDE.md     📖 This file
│
├─ Test files:
│  ├─ diagnose_chatbot.py              🧪 Run first
│  ├─ test_chatbot_setup.py            🧪 Verify config
│  └─ test_chatbot_endpoint.py         🧪 Test endpoint
│
└─ Other files... (unchanged)
```

---

## 🚀 Quick Command Reference

### Setup & Testing
```powershell
# Navigate to project
cd d:\Desktop\C_A_D_S

# Install dependencies
pip install -r requirements.txt

# Run diagnostics (easiest first)
python diagnose_chatbot.py
python test_chatbot_setup.py
python test_chatbot_endpoint.py

# Start app
python app.py
```

### Stopping the App
```
In PowerShell: Ctrl+C
In browser: Close or navigate away
```

### Checking API Key
```powershell
# See if .env file exists
dir .env

# See .env content
type .env

# Check if environmental variable is loaded
$env:OPENAI_API_KEY
```

---

## ⚡ Common Commands Cheat Sheet

| Command | What it does |
|---------|------------|
| `cd d:\Desktop\C_A_D_S` | Navigate to project |
| `pip install -r requirements.txt` | Install packages |
| `python app.py` | Start Flask server |
| `python diagnose_chatbot.py` | Run diagnostic test |
| `python test_chatbot_setup.py` | Test setup |
| `python test_chatbot_endpoint.py` | Test endpoint |
| `Ctrl+C` | Stop running app |
| `pip show requests` | Check package details |

---

## 🎓 How It Works (Simple Explanation)

```
You ask chatbot a question
         ↓
Browser sends to /chatbot_api
         ↓
Python backend receives request
         ↓
Checks .env for OPENAI_API_KEY
         ↓
Sends request to OpenAI servers
         ↓
OpenAI returns AI-generated answer
         ↓
Browser displays answer
```

If OpenAI API fails:
```
         ↓
Fallback to local database
         ↓
Returns pre-configured answer
         ↓
Browser displays answer
```

---

## ✅ Success Checklist

- [ ] Created `.env` file in project root
- [ ] Added `OPENAI_API_KEY=sk-...` to `.env`
- [ ] Ran `pip install -r requirements.txt`
- [ ] Ran `python diagnose_chatbot.py` - all ✓
- [ ] Started app with `python app.py`
- [ ] Opened http://localhost:5000
- [ ] Started a lab
- [ ] Clicked ghost icon (chatbot)
- [ ] Asked a question
- [ ] Got an AI response ✓

If all checked, you're done! 🎉

---

## 🆘 Need Help?

### Still stuck? Try this order:
1. **Easiest first:** Run `python diagnose_chatbot.py`
   - Tells you exactly what's wrong
   
2. **Check logs:** Watch PowerShell window when app runs
   - Look for [ERROR] or [WARNING] messages
   
3. **Browser console:** F12 → Console tab
   - Check for JavaScript errors
   
4. **Review .env:** Verify file has your real API key
   - Not the placeholder!
   
5. **Check API key:** https://platform.openai.com/account/usage/overview
   - Make sure it's active and not rate-limited

### Still need help?
See the full guides:
- `CHATBOT_QUICK_START.md` - 5 minute overview
- `CHATBOT_API_INTEGRATION_GUIDE.md` - Complete reference
- `CHATBOT_IMPLEMENTATION_SUMMARY.md` - Full documentation

---

## 💡 Pro Tips

💡 **Always test locally first** before deploying

💡 **Keep .env out of git** - it contains your API key!

💡 **Use `gpt-3.5-turbo`** for faster/cheaper responses

💡 **Monitor API usage** - you may have rate limits

💡 **Save responses** - avoid repeated API calls for same question

---

## 🎉 You Made It!

Congratulations! Your chatbot is now:
✓ Using AI-powered responses
✓ Keeping your API key secure
✓ Falling back gracefully if API fails
✓ Ready for production use

**Next time:**
1. `python app.py`
2. Open http://localhost:5000
3. Enjoy your chatbot! 🤖

---

*Last Updated: February 17, 2026*
*Version: 1.0 - Complete Implementation*
