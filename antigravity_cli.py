#!/usr/bin/env python3
import sys
import json
import urllib.request

def chat_loop():
    print("=======================================================================")
    print("🚀 Google Antigravity Universal Engine - Interactive SSH CLI Interface")
    print("Connected to Microservice on Docker Container (port 5005)")
    print("Type your questions or instructions below. Type 'exit' or 'quit' to stop.")
    print("=======================================================================\n")

    while True:
        try:
            prompt = input("Antigravity> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Antigravity CLI. Goodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in ["exit", "quit", "q"]:
            print("Exiting Antigravity CLI. Goodbye!")
            break

        url = "http://localhost:5005/chat"
        payload = json.dumps({"prompt": prompt}).encode('utf-8')
        headers = {'Content-Type': 'application/json'}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                response_text = res_json.get("response", "")
                print(f"\n{response_text}\n")
        except Exception as e:
            print(f"\n[Error connecting to Antigravity Docker Microservice]: {e}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
        url = "http://localhost:5005/chat"
        payload = json.dumps({"prompt": user_prompt}).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_json = json.loads(resp.read().decode('utf-8'))
                print(res_json.get("response", ""))
        except Exception as e:
            print(f"[Error]: {e}")
    else:
        chat_loop()
