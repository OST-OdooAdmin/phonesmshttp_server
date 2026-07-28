#!/usr/bin/env python3
"""
Google Antigravity Universal Engine - Interactive SSH CLI
Connects to the Antigravity Docker Microservice on port 5005.

Usage:
  Interactive mode:  antigravity
  One-shot mode:     antigravity "your question here"
  Circuit breaker:   antigravity --status
  Set API keys:      antigravity --set-key GEMINI_API_KEY=AIzaSy...
"""
import sys
import json
import urllib.request

SERVICE_URL = "http://localhost:5005"

def post_chat(prompt):
    url = f"{SERVICE_URL}/chat"
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_status():
    url = f"{SERVICE_URL}/circuit-breaker"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))

def set_api_key(key_value):
    parts = key_value.split("=", 1)
    if len(parts) != 2:
        print("Usage: antigravity --set-key KEY_NAME=key_value")
        return
    key_name, key_val = parts
    url = f"{SERVICE_URL}/api-keys"
    payload = json.dumps({"api_keys": {key_name: key_val}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"✅ {data.get('message', 'Key updated')}")

def print_status():
    data = get_status()
    print("\n========== CIRCUIT BREAKER STATUS ==========")
    for p in data.get("providers", []):
        icon = "✅" if p.get("available") else "⏸️"
        status = "Available" if p.get("available") else f"Isolated ({p.get('reason', 'N/A')}, reset in {p.get('reset_in_seconds', '?')}s)"
        print(f"  {icon} [{p.get('credit_pool', '?').upper()}] {p['name']}: {status}")
    print("=============================================\n")

def print_switch_log(switch_log):
    if switch_log:
        print("\n--- Auto-Switch Log ---")
        for entry in switch_log:
            print(f"  {entry}")
        print("-----------------------")

def chat_loop():
    print("=======================================================================")
    print("🚀 Google Antigravity Universal Engine - Auto-Switch Multi-Provider CLI")
    print("Connected to Docker Container on port 5005")
    print("")
    print("Commands:")
    print("  Type your question or instruction to get an AI response")
    print("  /status     - View circuit breaker & provider availability")
    print("  /setkey     - Configure an API key (e.g., /setkey GEMINI_API_KEY=AIza...)")
    print("  exit / quit - Exit the CLI")
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
        if prompt.lower() in ("/status", "--status", "status"):
            try:
                print_status()
            except Exception as e:
                print(f"[Error]: {e}")
            continue
        if prompt.lower().startswith("/setkey "):
            try:
                set_api_key(prompt[8:].strip())
            except Exception as e:
                print(f"[Error]: {e}")
            continue

        try:
            result = post_chat(prompt)
            response_text = result.get("response", "")
            provider = result.get("provider_used", "Unknown")
            switch_log = result.get("switch_log", [])
            query_count = result.get("query_count", "?")

            print(f"\n{response_text}")
            print(f"\n  [Provider: {provider} | Query #{query_count}]")
            print_switch_log(switch_log)
            print("")
        except Exception as e:
            print(f"\n[Error connecting to Antigravity Docker Microservice]: {e}\n")

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        chat_loop()
    elif args[0] in ("--status", "-s", "status"):
        try:
            print_status()
        except Exception as e:
            print(f"[Error]: {e}")
    elif args[0] == "--set-key" and len(args) > 1:
        try:
            set_api_key(args[1])
        except Exception as e:
            print(f"[Error]: {e}")
    else:
        prompt = " ".join(args)
        try:
            result = post_chat(prompt)
            print(result.get("response", ""))
            switch_log = result.get("switch_log", [])
            print_switch_log(switch_log)
        except Exception as e:
            print(f"[Error]: {e}")
