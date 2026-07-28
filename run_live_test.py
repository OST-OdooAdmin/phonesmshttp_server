import urllib.request
import json
import ssl
import sys

ctx = ssl._create_unverified_context()
key = sys.argv[1] if len(sys.argv) > 1 else ""

urls = [
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
    f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
]

prompt = "is the junk in sarawak kuching open at night? is there any food available to consume there?"
payload = {"contents": [{"parts": [{"text": prompt}]}]}
headers = {"Content-Type": "application/json"}

for url in urls:
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print("LIVE_API_SUCCESS:", text)
            break
    except Exception as e:
        print("LIVE_API_ERROR FOR", url, ":", e)
