import json, urllib.request

url = "http://localhost:5005/chat"
p = "What are the top 3 best practices when designing microservices architecture in Python?"
req = urllib.request.Request(url, data=json.dumps({"prompt": p}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(data.get("response", ""))
