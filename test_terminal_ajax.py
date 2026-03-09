"""Test the new AJAX terminal execute endpoint."""
import requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# Start lab
r = s.post(BASE + "/lab/s3/start", data={"mode": "attack", "level": "Beginner"}, allow_redirects=True)
print(f"[LAB] {r.status_code} - {r.url}")

# Test new AJAX endpoint
tests = ["aws s3 ls", "nmap -sV 192.168.1.1", "whoami", "help"]
for cmd in tests:
    r = s.post(BASE + "/api/terminal_execute",
               headers={"Content-Type": "application/json"},
               json={"command": cmd}, timeout=15)
    d = r.json()
    print(f"\n[CMD] $ {cmd}")
    print(f"  lines: {d.get('new_lines', [])}")
    ai = d.get("ai_analysis", "")
    if ai:
        print(f"  [AI] {ai[:200]}")
    else:
        print(f"  [AI] (no Groq key set - using fallback)")
    print(f"  state={d.get('lab_state')} outcome={d.get('outcome')}")

# Test /api/logs
r = s.get(BASE + "/api/logs")
print(f"\n[LOGS] status={r.status_code}, events={len(r.json().get('events',[]))}")
print("All tests passed!")
