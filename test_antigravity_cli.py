#!/usr/bin/env python3
import json, urllib.request
url = "http://localhost:5005/chat"
prompt = "is the swimming pool in singapore yio chu kang open today"
payload = json.dumps({"prompt": prompt}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(data.get("response", ""))
