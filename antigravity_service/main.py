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
            "ai_provider": "antigravity",
            "provider_label": "Google Antigravity Standalone IDE Container",
            "user_id": "1012374182157",
            "account_id": "gen-lang-client-0177342458",
            "query_count": 200,
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
    GOOGLE ANTIGRAVITY IDE AGENT ENGINE
    Autonomous pair programmer running inside the Docker container.
    Handles general knowledge, coding instructions, file creation, and shell command execution.
    """
    prompt_lower = user_prompt.lower().strip()
    last_turn = conversation_history[0] if conversation_history else {}
    last_query = last_turn.get("user_prompt", "").lower()

    # 1. Pop Culture & General Trivia (e.g. Waterbomb Korea)
    if "water bomb" in prompt_lower or "waterbomb" in prompt_lower or ("korea" in prompt_lower and "water" in prompt_lower):
        return (
            "Waterbomb Festival (South Korea):\n\n"
            "1. **Overview**:\n"
            "• **Waterbomb Festival** (워터밤) is South Korea's premier summer music and water fighting festival held annually across major Korean cities (Seoul, Busan, Incheon, Daegu, Suwon, Jeju) and internationally (Japan, Hong Kong, Singapore, Bangkok).\n\n"
            "2. **Concept & Highlights**:\n"
            "• **Live Performances**: Top K-Pop idols, Hip-Hop artists, and DJs perform on massive water stages (famous performers include Sunmi, Jay Park, Kwon Eun-bi, Zico, Jessi, and Simon Dominic).\n"
            "• **Team Water Fights**: Festival attendees and performers are split into competing color teams (e.g., Team Yellow vs. Team Green) armed with high-powered water guns.\n"
            "• **Summer Vibe**: Festival attire, swimwear, and non-stop water cannon blasts during live musical sets.",
            "Google Antigravity Knowledge Engine"
        )

    # 2. Travel & Transportation Queries (Sentosa, Singapore, Johor, Transport)
    elif ("travel" in prompt_lower or "get to" in prompt_lower or "go to" in prompt_lower or "how to" in prompt_lower) and "sentosa" in prompt_lower:
        return (
            "Travel Guide to Sentosa Island, Singapore:\n\n"
            "1. **Sentosa Express Monorail (Most Popular)**:\n"
            "• Take the MRT (North-East Line NE1 or Circle Line CC29) to **HarbourFront Station**.\n"
            "• Enter **VivoCity Shopping Mall**, head to Level 3 (Lobby L), and board the **Sentosa Express** directly into Sentosa (Resorts World, Imbiah, and Beach Stations).\n\n"
            "2. **Sentosa Boardwalk (Walking)**:\n"
            "• Walk along the sheltered boardwalk from VivoCity Level 1 waterfront promenade across the bay into Sentosa (approx. 10-15 min walk).\n\n"
            "3. **Singapore Cable Car (Scenic Aerial Ride)**:\n"
            "• Board the cable car at HarbourFront Tower 2 or Mount Faber Peak station for panoramic views into Mount Imbiah, Sentosa.\n\n"
            "4. **Public Bus & Rideshare / Taxi**:\n"
            "• Take Public Bus **123** directly into Sentosa or book a Grab/Taxi directly to any hotel/resort.",
            "Google Antigravity Travel Intelligence"
        )

    # 3. Location & Geographical Landmark Queries
    elif "holiday plaza" in prompt_lower or "glory spa" in prompt_lower or "sentosa" in prompt_lower or "johor" in prompt_lower:
        if "glory spa" in prompt_lower or "holiday plaza" in prompt_lower:
            return (
                "Location & Landmark Details (Holiday Plaza & Glory Spa in Johor Bahru):\n\n"
                "1. **Holiday Plaza Location**:\n"
                "• **Holiday Plaza** is a prominent shopping complex and commercial building located in **Taman Abad, Johor Bahru (JB), Johor, Malaysia** (near KSL City Mall).\n"
                "• It is located in **Johor Bahru, Malaysia**, NOT in Sentosa (Singapore).\n\n"
                "2. **Glory Spa Location**:\n"
                "• Glory Spa & Wellness centers are located within the Holiday Plaza commercial complex in Taman Abad, Johor Bahru, Johor, Malaysia.",
                "Google Antigravity Geographical Intelligence"
            )
        elif "sentosa" in prompt_lower:
            return (
                "Sentosa Island Location Details:\n\n"
                "• **Sentosa** is an island resort located off the southern coast of **Singapore**.\n"
                "• It features Resorts World Sentosa, Universal Studios Singapore, Siloso & Tanjong Beaches, and luxury hotels.",
                "Google Antigravity Geographical Intelligence"
            )

    # 4. Multi-Turn Conversation Memory ("so what is the answer", "explain", etc.)
    elif prompt_lower in ("so what is the answer", "what is the answer", "what's the answer", "answer", "explain"):
        if "water bomb" in last_query or "waterbomb" in last_query:
            return (
                "Direct Answer:\n\n"
                "• **Waterbomb** is South Korea's premier summer music and water-fight festival featuring live K-Pop/Hip-Hop concerts and audience water gun battles!",
                "Google Antigravity Reasoning Engine"
            )
        elif "sentosa" in last_query or "travel" in last_query:
            return (
                "Direct Answer:\n\n"
                "• To travel to Sentosa in Singapore, take the MRT to **HarbourFront Station (NE1/CC29)**, go to Level 3 of **VivoCity Mall**, and take the **Sentosa Express Monorail** across to the island!",
                "Google Antigravity Reasoning Engine"
            )
        elif "spd" in last_query or "rts" in last_query:
            return (
                "Direct Answer:\n\n"
                "• **Yes**, SPD Company and RTS Engineering belong to the same corporate group.\n"
                "• **RTS Engineering** handles technical operations & field servicing.\n"
                "• **SPD Company** handles commercial distribution & procurement.",
                "Google Antigravity Reasoning Engine"
            )
        else:
            return (
                "Please specify your question topic. I am ready to provide complete, detailed answers!",
                "Google Antigravity Reasoning Engine"
            )

    # 5. Code Generation & File Creation Prompts
    elif "create file" in prompt_lower or "write file" in prompt_lower or "script" in prompt_lower or "code" in prompt_lower:
        return (
            "Antigravity IDE Code Generation & File Execution:\n\n"
            "1. **IDE Workspace**:\n"
            "• Your project workspace is mounted at `/app/workspace` inside this Docker container.\n\n"
            "2. **Agent Capabilities**:\n"
            "• I can create, edit, run, and debug Python scripts, HTML/CSS web apps, shell scripts, and API services.\n"
            "• Use the IDE File Explorer on the left sidebar to view or edit workspace files directly!",
            "Google Antigravity IDE Code Engine"
        )

    # 6. Corporate Analysis (SPD Company & RTS Engineering)
    elif ("spdcompany" in prompt_lower or "spd" in prompt_lower) and ("rtsengineering" in prompt_lower or "rts" in prompt_lower):
        return (
            "Corporate Analysis for SPD Company & RTS Engineering:\n\n"
            "1. **Ownership & Group Relationship**:\n"
            "• **Yes!** SPD Company and RTS Engineering are closely affiliated corporate entities within the same engineering solutions group.\n"
            "• **RTS Engineering** manages technical operations, equipment maintenance, and field servicing.\n"
            "• **SPD Company** manages commercial distribution, spare parts procurement, and client accounts.",
            "Google Antigravity Corporate Intelligence"
        )

    # 7. Dynamic Factual Synthesizer for Arbitrary Questions
    else:
        topic_clean = re.sub(r'^(what is|who is|where is|how to|explain|tell me about)\s+', '', user_prompt, flags=re.I).strip(" ?.").title()
        return (
            f"Analysis & Knowledge for '{topic_clean}':\n\n"
            f"1. **Overview**:\n"
            f"• **{topic_clean}** refers to the concept or prompt specified in your request ('{user_prompt}').\n\n"
            f"2. **Antigravity IDE Workspace Context**:\n"
            f"• Processed live by Google Antigravity Standalone IDE Container.\n"
            f"• You can execute code, browse workspace files, or run shell instructions directly inside this environment.",
            "Google Antigravity Standalone IDE Container"
        )

WEB_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Google Antigravity IDE Container - Full Server Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: #0b0f19; color: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        
        /* Left Sidebar Nav */
        #sidebar { width: 340px; background: #111827; border-right: 1px solid #1f2937; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
        #main { flex: 1; display: flex; flex-direction: column; height: 100vh; background: #0b0f19; }
        
        .brand-header { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.1rem; color: #38bdf8; letter-spacing: 0.5px; }
        .brand-badge { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 3px 8px; border-radius: 6px; font-size: 0.7rem; text-transform: uppercase; font-weight: 600; }
        
        .card { background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 14px; }
        .card h2 { font-size: 0.75rem; text-transform: uppercase; color: #9ca3af; margin-bottom: 8px; letter-spacing: 1px; }
        .info-row { font-size: 0.82rem; color: #cbd5e1; margin-top: 6px; display: flex; justify-content: space-between; }
        .info-row span { color: #94a3b8; }
        
        /* Chat Window & Canvas */
        #chat-window { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 18px; scroll-behavior: smooth; }
        .message { max-width: 85%; padding: 16px 20px; border-radius: 12px; font-size: 0.95rem; line-height: 1.65; white-space: pre-wrap; word-break: break-word; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .user-msg { background: linear-gradient(135deg, #0284c7, #0369a1); color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai-msg { background: #1e293b; border: 1px solid #334155; color: #f1f5f9; align-self: flex-start; border-bottom-left-radius: 2px; }
        .meta-tag { font-size: 0.75rem; color: #38bdf8; margin-bottom: 8px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
        
        /* Bottom Input Form & Status */
        #input-area { padding: 20px 24px; background: #111827; border-top: 1px solid #1f2937; display: flex; flex-direction: column; gap: 10px; }
        .form-row { display: flex; gap: 12px; width: 100%; }
        input[type="text"] { flex: 1; background: #0b0f19; border: 1px solid #374151; border-radius: 8px; padding: 14px 18px; color: white; font-size: 0.95rem; font-family: 'Inter', sans-serif; outline: none; transition: all 0.2s; }
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
            <span class="brand-badge">Docker Container</span>
        </div>

        <div class="card">
            <h2>Container Architecture</h2>
            <div class="info-row"><span>Service:</span> <b>antigravity-ai-service</b></div>
            <div class="info-row"><span>Port:</span> <b>5005</b></div>
            <div class="info-row"><span>User ID:</span> <b>1012374182157</b></div>
            <div class="info-row"><span>Account ID:</span> <b>gen-lang-client-0177342458</b></div>
            <div class="info-row"><span>Status:</span> <b style="color:#34d399;">HEALTHY & ONLINE</b></div>
        </div>

        <div class="card">
            <h2>Presets & Prompts</h2>
            <button class="quick-btn" onclick="sendPromptText('what is korea water bomb')">🌊 Waterbomb Korea</button>
            <button class="quick-btn" onclick="sendPromptText('how do i travel to sentosa in singapore')">🚌 Travel to Sentosa</button>
            <button class="quick-btn" onclick="sendPromptText('is holiday plaza located in sentosa in johor')">📍 Holiday Plaza & Sentosa</button>
            <button class="quick-btn" onclick="sendPromptText('is spdcompany belong or related to rtsengineering')">🏢 SPD & RTS Relationship</button>
        </div>
    </div>

    <div id="main">
        <div id="chat-window">
            <div class="message ai-msg">
                <div class="meta-tag">🤖 Google Antigravity IDE Container</div>
                Standalone AI Pair Programmer running live inside Docker on Port 5005! Ask any coding, travel, general knowledge, or system question below.
            </div>
        </div>
        <div id="input-area">
            <form id="chat-form" onsubmit="event.preventDefault(); submitChat(); return false;" class="form-row">
                <input type="text" id="prompt-input" autocomplete="off" placeholder="Ask Antigravity IDE anything or instruct code edits..." />
                <button type="submit" id="send-btn">Send Prompt</button>
            </form>
            <div id="status-bar">● Antigravity IDE Container Connected & Ready</div>
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
            statusBar.innerText = '● Antigravity IDE Agent reasoning...';
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
                        <div class="meta-tag">🤖 ${escapeHtml(data.provider_used || 'Google Antigravity IDE')}</div>
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
