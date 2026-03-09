import requests

BASE = "http://127.0.0.1:5000"

s = requests.Session()

# Start S3 lab
resp = s.post(BASE + "/lab/s3/start", data={"mode": "attack", "level": "Beginner"}, allow_redirects=True)
print(f"[LAB START] status={resp.status_code}, url={resp.url}")

# Test chatbot
resp = s.post(
    BASE + "/chatbot_api",
    headers={"Content-Type": "application/json"},
    json={"message": "How do I do reconnaissance on an S3 bucket?"},
    timeout=30,
)
print(f"[CHATBOT] status={resp.status_code}")
data = resp.json()
reply = data.get("reply", "(no reply)")
print(f"[CHATBOT] reply ({len(reply)} chars):")
print(reply[:400])
