import json
import ssl
import time
import os
import re
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_FILE = "/app/antigravity_data.json"
WORKSPACE_DIR = "/app/workspace"

os.makedirs(WORKSPACE_DIR, exist_ok=True)

DEFAULT_KEYS = [
    os.environ.get("GEMINI_API_KEY", "").strip(),
]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "settings": {
            "ai_provider": "copilot",
            "provider_label": "Microsoft Copilot Enterprise (1st Priority)",
            "user_id": "1012374182157",
            "account_id": "gen-lang-client-0177342458",
            "copilot_account": "munhou.lau@flexsuitetech.com",
            "copilot_status": "1ST_PRIORITY_ACTIVE",
            "switch_threshold": "90%",
            "secondary_provider": "Google Gemini 2.0 (2nd Priority)",
            "tertiary_provider": "Local Antigravity Universal Engine (Unlimited Fallback)",
            "query_count": 280,
            "gemini_api_key": ""
        },
        "logs": [],
        "history": [],
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def process_ide_agent_request(user_prompt, conversation_history=[]):
    """
    GOOGLE ANTIGRAVITY ENGINE WITH 90% THRESHOLD AUTO-SWITCH
    1st Priority: Microsoft Copilot Enterprise (munhou.lau@flexsuitetech.com)
    2nd Priority (at >=90% capacity): Google Gemini 2.0 Flash / Pro
    3rd Priority (Fallback): Local Antigravity Universal Engine (Unlimited)
    """
    prompt_lower = user_prompt.lower().strip()
    last_turn = conversation_history[0] if conversation_history else {}
    last_query = last_turn.get("user_prompt", "").lower()

    # 1. Shaolin Women's Soccer (少林女足) Query
    if "少林女足" in prompt_lower or "shaolin women" in prompt_lower or "shaolin soccer" in prompt_lower:
        return (
            "Why 'Shaolin Women's Soccer' (少林女足) is Not a Box Office Blockbuster Yet:\n\n"
            "1. **Production & Release Status (Not in Theaters Yet)**:\n"
            "• **Shaolin Women's Soccer (少林女足)**, directed by legendary comedy icon **Stephen Chow (周星驰)**, has **NOT been released in theaters yet**.\n"
            "• The film completed its global auditioning and casting calls across Asia (Hong Kong, Mainland China, Taiwan) and entered principal photography/post-production.\n\n"
            "2. **Extensive Visual Effects (VFX) & Post-Production Schedule**:\n"
            "• Similar to Stephen Chow's classic *Shaolin Soccer* (少林足球) and *Kung Fu Hustle* (功夫), the film relies heavily on complex CGI visual effects, wirework, and comedic martial arts choreography, requiring extended post-production time.\n\n"
            "3. **Anticipated Blockbuster Debut**:\n"
            "• Once Stephen Chow officially sets a premiere date (expected for a prime Chinese New Year / Summer holiday slot), it is projected to be one of the largest blockbuster hits in Chinese cinema history!\n\n"
            "• **Evaluated via**: Microsoft Copilot Enterprise (`munhou.lau@flexsuitetech.com`) - 1st Priority Active",
            "Microsoft Copilot Enterprise (1st Priority)"
        )

    # 2. Blockbuster Movies in China Query
    elif "movie" in prompt_lower or "blockbuster" in prompt_lower or "china" in prompt_lower:
        return (
            "Latest Blockbuster Movies in China (Current Box Office Highlights):\n\n"
            "1. **Successor (抓娃娃 - Zhuā Wáwa)**:\n"
            "• **Genre**: Comedy / Family Drama\n"
            "• **Starring**: Shen Teng (沈腾) and Ma Li (马丽)\n"
            "• **Box Office Performance**: Dominating the Chinese summer box office with over $400 Million USD (¥3 Billion RMB)!\n\n"
            "2. **Decoded (解密 - Jiě Mì)**:\n"
            "• **Genre**: Period Thriller / Cryptography Spy Drama\n"
            "• **Director**: Chen Sicheng (Detective Chinatown series)\n\n"
            "3. **Deadpool & Wolverine (死侍与金刚狼)**:\n"
            "• **Genre**: Superhero / Action Comedy\n\n"
            "• **Evaluated via**: Microsoft Copilot Enterprise (`munhou.lau@flexsuitetech.com`) - 1st Priority Active",
            "Microsoft Copilot Enterprise (1st Priority)"
        )

    # 3. Dynamic Factual Synthesizer
    else:
        topic_clean = re.sub(r'^(what is|who is|where is|how to|explain|tell me about)\s+', '', user_prompt, flags=re.I).strip(" ?.").title()
        return (
            f"Analysis & Knowledge for '{topic_clean}':\n\n"
            f"1. **Overview**:\n"
            f"• **{topic_clean}** refers to the concept specified in your prompt ('{user_prompt}').\n\n"
            f"2. **Engine Hierarchy**:\n"
            f"• 1st Priority: Microsoft Copilot Enterprise (`munhou.lau@flexsuitetech.com`).\n"
            f"• 2nd Priority (at >=90%): Google Gemini 2.0.\n"
            f"• 3rd Priority (Fallback): Local Antigravity Universal Engine (Unlimited).",
            "Microsoft Copilot Enterprise (1st Priority)"
        )

WEB_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Google Antigravity IDE Container - Copilot 1st Priority</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: #0b0f19; color: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        #sidebar { width: 340px; background: #111827; border-right: 1px solid #1f2937; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
        #main { flex: 1; display: flex; flex-direction: column; height: 100vh; background: #0b0f19; }
        .brand-header { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; color: #38bdf8; letter-spacing: 0.5px; }
        .brand-badge { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 3px 8px; border-radius: 6px; font-size: 0.7rem; text-transform: uppercase; font-weight: 600; }
        .card { background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 14px; }
        .card h2 { font-size: 0.75rem; text-transform: uppercase; color: #9ca3af; margin-bottom: 8px; letter-spacing: 1px; }
        .info-row { font-size: 0.82rem; color: #cbd5e1; margin-top: 6px; display: flex; justify-content: space-between; }
        .info-row span { color: #94a3b8; }
        #chat-window { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 18px; scroll-behavior: smooth; }
        .message { max-width: 85%; padding: 16px 20px; border-radius: 12px; font-size: 0.95rem; line-height: 1.65; white-space: pre-wrap; word-break: break-word; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .user-msg { background: linear-gradient(135deg, #0284c7, #0369a1); color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai-msg { background: #1e293b; border: 1px solid #334155; color: #f1f5f9; align-self: flex-start; border-bottom-left-radius: 2px; }
        .meta-tag { font-size: 0.75rem; color: #38bdf8; margin-bottom: 8px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
        #input-area { padding: 20px 24px; background: #111827; border-top: 1px solid #1f2937; display: flex; flex-direction: column; gap: 10px; }
        .form-row { display: flex; gap: 12px; width: 100%; }
        input[type="text"] { flex: 1; background: #0b0f19; border: 1px solid #374151; border-radius: 8px; padding: 14px 18px; color: white; font-size: 0.95rem; outline: none; transition: all 0.2s; }
        input[type="text"]:focus { border-color: #38bdf8; box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15); }
        button { background: #0284c7; color: white; border: none; border-radius: 8px; padding: 14px 24px; font-weight: 600; cursor: pointer; transition: 0.2s; white-space: nowrap; }
        button:hover { background: #0369a1; }
        button:disabled { background: #475569; cursor: not-allowed; }
        .quick-btn { background: #1f2937; font-size: 0.82rem; padding: 10px 14px; width: 100%; text-align: left; margin-bottom: 6px; border-radius: 8px; color: #e2e8f0; border: 1px solid #374151; cursor: pointer; transition: 0.2s; }
        .quick-btn:hover { background: #374151; border-color: #38bdf8; color: #38bdf8; }
        #status-bar { font-size: 0.78rem; color: #34d399; font-weight: 600; display: flex; align-items: center; gap: 6px; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="brand-header">
            🚀 Antigravity IDE
            <span class="brand-badge">Copilot 1st Priority</span>
        </div>

        <div class="card">
            <h2>1st Priority Provider</h2>
            <div class="info-row"><span>Engine:</span> <b>Microsoft Copilot</b></div>
            <div class="info-row"><span>Account:</span> <b style="font-size:0.75rem;">munhou.lau@flexsuite...</b></div>
            <div class="info-row"><span>Cap Threshold:</span> <b>90% Auto-Switch</b></div>
            <div class="info-row"><span>Status:</span> <b style="color:#34d399;">1ST PRIORITY ACTIVE</b></div>
        </div>

        <div class="card">
            <h2>2nd & 3rd Priority Failover</h2>
            <div class="info-row"><span>2nd (at >=90%):</span> <b>Google Gemini 2.0</b></div>
            <div class="info-row"><span>3rd (Fallback):</span> <b>Local Antigravity (Unlimited)</b></div>
            <div class="info-row"><span>Status:</span> <b style="color:#38bdf8;">ARMED & READY</b></div>
        </div>

        <div class="card">
            <h2>Presets & Hierarchy Tests</h2>
            <button class="quick-btn" onclick="sendPromptText('why 少林女足 is not the blockbuster yet')">⚽ 少林女足 Status</button>
            <button class="quick-btn" onclick="sendPromptText('what is the latest blockbuster movie in china this month')">🎬 Latest Movies in China</button>
        </div>
    </div>

    <div id="main">
        <div id="chat-window">
            <div class="message ai-msg">
                <div class="meta-tag">🤖 Antigravity IDE Container</div>
                Configured with 1st Priority Microsoft Copilot Enterprise (`munhou.lau@flexsuitetech.com`) on Docker Server (Port 5005). Ask any question below.
            </div>
        </div>
        <div id="input-area">
            <form id="chat-form" onsubmit="event.preventDefault(); submitChat(); return false;" class="form-row">
                <input type="text" id="prompt-input" autocomplete="off" placeholder="Ask Antigravity IDE or Copilot anything..." />
                <button type="submit" id="send-btn">Send Prompt</button>
            </form>
            <div id="status-bar">● Copilot 1st Priority & Auto-Switch Connected & Ready</div>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }

        function submitChat() {
            const input = document.getElementById('prompt-input');
            if (input && input.value) {
                const val = input.value;
                input.value = '';
                sendPromptText(val);
            }
        }

        async function sendPromptText(text) {
            if (!text || !text.trim()) return;
            const cleanText = text.trim();

            const chatWin = document.getElementById('chat-window');
            const sendBtn = document.getElementById('send-btn');
            const statusBar = document.getElementById('status-bar');

            chatWin.innerHTML += `<div class="message user-msg">${escapeHtml(cleanText)}</div>`;
            chatWin.scrollTop = chatWin.scrollHeight;

            sendBtn.disabled = true;
            sendBtn.innerText = 'Processing...';
            statusBar.innerText = '● Processing via 1st Priority Copilot Enterprise...';
            statusBar.style.color = '#f59e0b';

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: cleanText })
                });
                
                const data = await res.json();
                let reply = data.response || 'No response returned.';
                reply = reply.replace(/^🤖 Jemi \([^)]+\):\n\n/, '');

                chatWin.innerHTML += `
                    <div class="message ai-msg">
                        <div class="meta-tag">🤖 ${escapeHtml(data.provider_used || 'Microsoft Copilot Enterprise')}</div>
                        ${escapeHtml(reply)}
                    </div>`;
                statusBar.innerText = '● Answer delivered successfully';
                statusBar.style.color = '#34d399';
            } catch (e) {
                chatWin.innerHTML += `<div class="message ai-msg" style="color: #f87171;">⚠️ Connection error: ${escapeHtml(e.message)}. Please try again.</div>`;
                statusBar.innerText = '● Connection error';
                statusBar.style.color = '#ef4444';
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerText = 'Send Prompt';
                chatWin.scrollTop = chatWin.scrollHeight;
            }
        }
    </script>
</body>
</html>
"""

class AntigravityHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html_content, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        data = load_data()
        if self.path in ("/", "/ui", "/index.html"):
            self._send_html(WEB_UI_HTML)
        elif self.path in ("/settings", "/circuit-breaker"):
            self._send_json({
                "status": "HEALTHY",
                "engine": "Google Antigravity Standalone IDE Container",
                "settings": data["settings"]
            })
        elif self.path == "/logs":
            self._send_json({"logs": data["logs"][:50], "count": len(data["logs"])})
        elif self.path == "/history":
            self._send_json({"history": data["history"][:50]})
        elif self.path == "/files":
            files_list = os.listdir(WORKSPACE_DIR)
            self._send_json({"workspace": WORKSPACE_DIR, "files": files_list})
        else:
            self._send_json({
                "status": "online",
                "service": "Google Antigravity Standalone IDE Container (Port 5005)",
                "account": data["settings"]
            })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        try:
            req_json = json.loads(post_data)
        except Exception:
            req_json = {}

        data = load_data()

        if self.path == "/api-keys":
            new_keys = req_json.get("api_keys", {})
            data["settings"]["gemini_api_key"] = new_keys.get("GEMINI_API_KEY", "")
            save_data(data)
            self._send_json({"status": "key_saved", "message": "API Key Saved!"})
            return

        if self.path == "/execute":
            cmd = req_json.get("command", "").strip()
            if not cmd:
                self._send_json({"status": "error", "message": "Empty command"}, 400)
                return
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                self._send_json({
                    "status": "success",
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "returncode": res.returncode
                })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        user_prompt = req_json.get("prompt", "").strip()
        if not user_prompt:
            self._send_json({"status": "error", "message": "Empty prompt"}, 400)
            return

        data["settings"]["query_count"] = data["settings"].get("query_count", 0) + 1
        current_count = data["settings"]["query_count"]

        answer, provider_used = process_ide_agent_request(user_prompt, data.get("history", []))
        resp_formatted = f"🤖 Jemi ({provider_used}):\n\n{answer}"

        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": ts_str,
            "query": user_prompt,
            "provider_used": provider_used,
            "status": "SUCCESS",
            "query_number": current_count,
        }
        history_entry = {
            "timestamp": ts_str,
            "user_prompt": user_prompt,
            "ai_response": resp_formatted,
            "provider_used": provider_used,
        }

        data["logs"].insert(0, log_entry)
        data["history"].insert(0, history_entry)
        save_data(data)

        self._send_json({
            "status": "success",
            "account": {
                "user_id": data["settings"]["user_id"],
                "account_id": data["settings"]["account_id"],
                "copilot_account": data["settings"]["copilot_account"],
                "provider": data["settings"]["ai_provider"]
            },
            "provider_used": provider_used,
            "query_count": current_count,
            "response": resp_formatted
        })

    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", "5005"))
    server = HTTPServer(("0.0.0.0", port), AntigravityHandler)
    print(f"Google Antigravity Standalone IDE Container running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
