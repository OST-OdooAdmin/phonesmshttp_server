import json, urllib.request

url = "http://localhost:5005/chat"
p = "why 少林女足 is not the blockblaster yet?"
req = urllib.request.Request(url, data=json.dumps({"prompt": p}).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(data.get("response", ""))
