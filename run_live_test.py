import urllib.request
import json
import ssl
import sys

ctx = ssl._create_unverified_context()
key = sys.argv[1] if len(sys.argv) > 1 else ""

models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
]

prompt = 'can odoo 19 do these "Summary Points: 1) Schedule Data Tracking: They need to log and track scheduled dates for Installation and Defect Rework. 2) Current Calendar Usage: The existing calendar is currently dedicated to the Sales team for site visits and appointments. 3) Separate Calendar Request: If a separate calendar can be set up in Odoo specifically for operations/servicing so it doesn\'t clutter or conflict with the sales calendar."'

payload = {"contents": [{"parts": [{"text": prompt}]}]}
headers = {"Content-Type": "application/json"}

for m in models:
    for ver in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{m}:generateContent?key={key}"
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"SUCCESS FOR {ver}/{m}:\n", text[:300])
                sys.exit(0)
        except Exception as e:
            print(f"FAILED FOR {ver}/{m}:", e)
