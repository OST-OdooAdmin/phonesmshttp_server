import json
import urllib.request

url = "http://localhost:5005/chat"

prompts = [
    "is spdcompany belong or related to rtsengineering",
    "are u link to odoo in current server in docker?",
    "is antigravity full version down here"
]

for prompt in prompts:
    print(f"\n=================== QUERY: '{prompt}' ===================")
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(data.get("response", ""))
