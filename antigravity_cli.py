#!/usr/bin/env python3
"""
Google Antigravity Universal Engine - Interactive SSH CLI
Connects to the Antigravity Docker Microservice on port 5005.

Usage:
  Interactive mode:  antigravity
  One-shot mode:     antigravity "your question here"
  Set API key:       antigravity --set-key GEMINI_API_KEY=AIzaSy...
"""
import sys
import json
import urllib.request

SERVICE_URL = "http://localhost:5005"

def post_chat(prompt):
    url = f"{SERVICE_URL}/chat"
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def set_api_key(key_pair):
    parts = key_pair.split("=", 1)
    if len(parts) != 2:
        print("Usage: antigravity --set-key KEY_NAME=KEY_VALUE")
        return
    key_name, key_val = parts[0].strip(), parts[1].strip()
    url = f"{SERVICE_URL}/api-keys"
    payload = json.dumps({"api_keys": {key_name: key_val}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"\n✅ {data.get('message', 'Key updated successfully!')}\n")

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
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        if prompt.startswith("--set-key "):
            set_api_key(prompt[10:].strip())
            continue

        try:
            result = post_chat(prompt)
            response_text = result.get("response", "")
            provider = result.get("provider_used", "Unknown")
            query_count = result.get("query_count", "?")

            print(f"\n{response_text}")
            print(f"\n[Provider: {provider} | Query #{query_count}]\n")
        except Exception as e:
            print(f"\n[Error connecting to Antigravity Docker Microservice]: {e}\n")

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        chat_loop()
    elif args[0] == "--set-key" and len(args) > 1:
        set_api_key(args[1])
    else:
        prompt = " ".join(args)
        if prompt.startswith("--set-key "):
            set_api_key(prompt[10:].strip())
        else:
            try:
                result = post_chat(prompt)
                print(result.get("response", ""))
            except Exception as e:
                print(f"[Error]: {e}")
