"""Quick setup checker for CADS platform."""
import os
import sys

# Load .env first
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] python-dotenv loaded")
except ImportError:
    print("[MISSING] python-dotenv — run: pip install python-dotenv")

checks = {
    "Flask installed": False,
    "requests installed": False,
    "pandas installed": False,
    "cyber_knowledge.json exists": os.path.exists("src/cyber_knowledge.json"),
    "database.db exists": os.path.exists("database.db"),
    "GROQ_API_KEY starts with gsk_": (os.environ.get("GROQ_API_KEY", "")).startswith("gsk_"),
}

try:
    import flask
    checks["Flask installed"] = True
except ImportError:
    pass

try:
    import requests
    checks["requests installed"] = True
except ImportError:
    pass

try:
    import pandas
    checks["pandas installed"] = True
except ImportError:
    pass

print()
all_ok = True
for k, v in checks.items():
    status = "OK" if v else "MISSING"
    print(f"  [{status}] {k}")
    if not v:
        all_ok = False

print()
if not checks["GROQ_API_KEY starts with gsk_"]:
    key_val = os.environ.get("GROQ_API_KEY", "(not set)")
    print(f"  [!] GROQ_API_KEY value: {key_val!r}")
    print("  [!] => Open .env and replace the placeholder with your real key from https://console.groq.com/keys")

if all_ok:
    print("All checks passed! Run: python app.py")
else:
    print("Fix the issues above, then run: python app.py")
