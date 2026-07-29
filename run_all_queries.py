import json, urllib.request

url = "http://localhost:5005/chat"

prompts = [
    "which version is this",
    "so what is the answer",
    "is spdcompany belong or related to rtsengineering"
]

for p in prompts:
    print(f"\n=================== QUERY: '{p}' ===================")
    req = urllib.request.Request(url, data=json.dumps({"prompt": p}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(data.get("response", ""))
