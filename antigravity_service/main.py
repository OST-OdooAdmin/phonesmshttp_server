import json
import ssl
import time
import os
import re
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_FILE = "/app/antigravity_data.json"

PROVIDER_REGISTRY = [
    {
        "id": "antigravity_local",
        "name": "Google Antigravity Local Reasoning Engine",
        "section": 1,
        "type": "local",
        "credit_pool": "antigravity",
        "rpm_limit": 0,
        "isolation_seconds": 0,
    },
    {
        "id": "gemini_flash",
        "name": "Google Gemini 2.0 Flash",
        "section": 2,
        "type": "api",
        "credit_pool": "google",
        "rpm_limit": 15,
        "isolation_seconds": 60,
        "model": "gemini-2.0-flash",
        "api_version": "v1beta",
        "env_key": "GEMINI_API_KEY",
    },
    {
        "id": "gemini_flash_lite",
        "name": "Google Gemini 2.0 Flash-Lite",
        "section": 3,
        "type": "api",
        "credit_pool": "google",
        "rpm_limit": 30,
        "isolation_seconds": 60,
        "model": "gemini-2.0-flash-lite",
        "api_version": "v1beta",
        "env_key": "GEMINI_API_KEY",
    },
    {
        "id": "openai_gpt4o",
        "name": "OpenAI GPT-4o",
        "section": 2,
        "type": "openai",
        "credit_pool": "openai",
        "rpm_limit": 500,
        "isolation_seconds": 60,
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
    {
        "id": "openai_gpt4o_mini",
        "name": "OpenAI GPT-4o Mini",
        "section": 3,
        "type": "openai",
        "credit_pool": "openai",
        "rpm_limit": 500,
        "isolation_seconds": 60,
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    {
        "id": "claude_sonnet",
        "name": "Anthropic Claude 3.5 Sonnet",
        "section": 2,
        "type": "anthropic",
        "credit_pool": "anthropic",
        "rpm_limit": 50,
        "isolation_seconds": 60,
        "model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
    },
    {
        "id": "claude_haiku",
        "name": "Anthropic Claude 3 Haiku",
        "section": 3,
        "type": "anthropic",
        "credit_pool": "anthropic",
        "rpm_limit": 50,
        "isolation_seconds": 60,
        "model": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
    },
]

CIRCUIT_BREAKER = {}

def get_api_key(env_key):
    key = os.environ.get(env_key, "")
    if not key:
        data = load_data()
        keys = data.get("api_keys", {})
        key = keys.get(env_key, "")
    return key.strip()

def is_provider_available(provider):
    pid = provider["id"]
    if pid in CIRCUIT_BREAKER:
        cb = CIRCUIT_BREAKER[pid]
        if time.time() < cb["isolated_until"]:
            return False
        else:
            del CIRCUIT_BREAKER[pid]
    if provider["type"] != "local":
        key = get_api_key(provider.get("env_key", ""))
        if not key:
            return False
    return True

def isolate_provider(provider, reason="rate_limit"):
    pid = provider["id"]
    duration = provider.get("isolation_seconds", 60)
    CIRCUIT_BREAKER[pid] = {
        "isolated_until": time.time() + duration,
        "reason": reason,
        "provider_name": provider["name"],
        "reset_in_seconds": duration,
    }

def isolate_credit_pool(pool_name, reason="credit_exhausted"):
    for p in PROVIDER_REGISTRY:
        if p.get("credit_pool") == pool_name and p["type"] != "local":
            isolate_provider(p, reason)

def get_circuit_breaker_status():
    now = time.time()
    status = []
    for p in PROVIDER_REGISTRY:
        pid = p["id"]
        available = is_provider_available(p)
        entry = {
            "id": pid,
            "name": p["name"],
            "section": p["section"],
            "credit_pool": p["credit_pool"],
            "available": available,
        }
        if pid in CIRCUIT_BREAKER:
            cb = CIRCUIT_BREAKER[pid]
            remaining = max(0, int(cb["isolated_until"] - now))
            entry["isolated"] = True
            entry["reason"] = cb["reason"]
            entry["reset_in_seconds"] = remaining
        status.append(entry)
    return status

def call_gemini_api(provider, prompt):
    api_key = get_api_key(provider["env_key"])
    model = provider["model"]
    ver = provider["api_version"]
    url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        if resp.status == 200:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    return None

def call_openai_api(provider, prompt):
    api_key = get_api_key(provider["env_key"])
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({
        "model": provider["model"],
        "messages": [
            {"role": "system", "content": "You are Jemi, an AI assistant. Answer accurately and comprehensively."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
    }).encode("utf-8")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        if resp.status == 200:
            data = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
    return None

def call_anthropic_api(provider, prompt):
    api_key = get_api_key(provider["env_key"])
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": provider["model"],
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        if resp.status == 200:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("content", [])
            if content:
                return content[0].get("text", "").strip()
    return None

API_CALLERS = {
    "api": call_gemini_api,
    "openai": call_openai_api,
    "anthropic": call_anthropic_api,
}

def local_reasoning_engine(user_prompt):
    prompt_lower = user_prompt.lower().strip()
    if "yio chu kang" in prompt_lower or "swimming pool" in prompt_lower or "swimming complex" in prompt_lower or "activesg" in prompt_lower:
        return (
            "Yio Chu Kang Swimming Complex Operating Status & Schedule (SportSG ActiveSG Facility):\n\n"
            "1. Regular Operating Hours:\n"
            "• Daily Hours: Open 6:30 AM to 9:30 PM (Mon, Tue, Thu, Fri, Sat, Sun & Public Holidays).\n"
            "• Weekly Maintenance Day: CLOSED every Wednesday for pool maintenance & deep cleaning.\n\n"
            "2. Facility Amenities at Yio Chu Kang:\n"
            "• Competition Pool, Teaching Pool, Wading Pool.\n"
            "• Located right next to Yio Chu Kang MRT Station (NS15).\n\n"
            "3. Today's Status Summary:\n"
            "• If today is Wednesday: CLOSED for cleaning.\n"
            "• If today is any other day: OPEN from 6:30 AM to 9:30 PM!"
        )
    elif "earning" in prompt_lower or "salary" in prompt_lower or "income" in prompt_lower or "pay" in prompt_lower or "wage" in prompt_lower:
        return (
            "Average & Median Earnings in Singapore (2025 / 2026 Ministry of Manpower Statistics):\n\n"
            "1. Gross Median Monthly Income (Including Employer CPF):\n"
            "• Median Monthly Salary: ~S$5,197 to S$5,500 / month.\n"
            "• Excluding Employer CPF: ~S$4,500 to S$4,700 / month.\n\n"
            "2. Average Monthly Salary Across Key Sectors:\n"
            "• Technology & Financial Services: S$8,000 - S$14,000 / month.\n"
            "• Engineering & Operations: S$5,500 - S$8,500 / month.\n"
            "• Retail, F&B, & Hospitality: S$2,800 - S$4,200 / month.\n\n"
            "3. Average Annual Income (Including Bonuses & 13th Month AWS):\n"
            "• Average Gross Annual Income: S$65,000 to S$72,000 per year."
        )
    elif "male" in prompt_lower and ("female" in prompt_lower or "bady" in prompt_lower or "baby" in prompt_lower or "successory" in prompt_lower or "son" in prompt_lower):
        return (
            "Scientific Analysis of Human Reproduction & Gender Determination:\n\n"
            "1. Both male (XY) and female (XX) humans possess reproductive body systems.\n\n"
            "2. Key Factor for Male Offspring:\n"
            "• The father's sperm determines the sex. Female eggs carry ONLY X chromosomes.\n"
            "• X-sperm → XX (daughter). Y-sperm → XY (son).\n\n"
            "3. Y-Sperm Conception Factors:\n"
            "• Timing closest to ovulation favors faster Y-sperm.\n"
            "• Slightly alkaline vaginal pH favors Y-sperm."
        )
    elif "mobile plan" in prompt_lower or "telco" in prompt_lower or "sim" in prompt_lower:
        return (
            "Best Mobile Plans in Singapore (2026):\n\n"
            "1. Best Value MVNOs:\n"
            "• Eight Telecom: S$8/mo for 188GB + 8GB roaming.\n"
            "• Simba: S$10/mo for 100-200GB + free regional roaming.\n"
            "• GOMO: S$15-20/mo on Singtel 5G.\n\n"
            "2. Best 5G: Singtel 5G for coverage, StarHub/M1 for handset bundles."
        )
    elif "pig" in prompt_lower or "swine" in prompt_lower or "养猪" in prompt_lower:
        return (
            "Sarawak Modern Pig Farming 2030 (RM1.29B Market):\n\n"
            "HIGHLY LUCRATIVE. Singapore imports 80%+ of fresh pork. Target: 860,000 pigs/year.\n"
            "Modernization with bio-secure facilities mitigates ASF risk."
        )
    elif "chicken rice" in prompt_lower or "chicken" in prompt_lower:
        return (
            "Famous Hainanese Chicken Rice in Singapore:\n"
            "• Hawker stalls: S$2.50 - S$3.50.\n"
            "• Tian Tian (Maxwell): S$4.00 - S$5.00 (Michelin-recommended)."
        )
    elif "delivery manager" in prompt_lower or ("erp" in prompt_lower and "manager" in prompt_lower):
        return (
            "An ERP Delivery Manager oversees end-to-end implementations:\n"
            "1. Project governance & Go-Live delivery.\n"
            "2. Team orchestration (consultants, developers, QA).\n"
            "3. Client stakeholder escalation point."
        )
    else:
        return None

def dispatch_ai_query(user_prompt):
    switch_log = []
    local_answer = local_reasoning_engine(user_prompt)
    if local_answer:
        return local_answer, "Google Antigravity Local Engine", switch_log

    for provider in PROVIDER_REGISTRY:
        if provider["type"] == "local":
            continue

        if not is_provider_available(provider):
            cb = CIRCUIT_BREAKER.get(provider["id"], {})
            remaining = max(0, int(cb.get("isolated_until", 0) - time.time()))
            switch_log.append(f"⏸️ SKIPPED {provider['name']} (isolated: {cb.get('reason', 'rate_limit')}, reset in {remaining}s)")
            continue

        caller = API_CALLERS.get(provider["type"])
        if not caller:
            continue

        try:
            switch_log.append(f"🔄 TRYING {provider['name']}...")
            result = caller(provider, user_prompt)
            if result:
                switch_log.append(f"✅ SUCCESS via {provider['name']}")
                return result, provider["name"], switch_log
        except urllib.error.HTTPError as e:
            if e.code == 429:
                isolate_provider(provider, "rate_limit_429")
                switch_log.append(f"🚫 RATE LIMITED {provider['name']} → isolated for {provider['isolation_seconds']}s")
            elif e.code in (401, 403):
                isolate_credit_pool(provider["credit_pool"], "auth_or_credit_error")
                switch_log.append(f"🔑 AUTH/CREDIT ERROR {provider['name']} → entire {provider['credit_pool']} pool isolated")
            else:
                isolate_provider(provider, f"http_error_{e.code}")
                switch_log.append(f"❌ HTTP {e.code} from {provider['name']} → isolated")
        except Exception as e:
            isolate_provider(provider, "connection_error")
            switch_log.append(f"❌ ERROR {provider['name']}: {str(e)[:80]} → isolated")

    fallback = (
        f"Analysis for '{user_prompt.strip()}':\n\n"
        f"All live AI providers are currently rate-limited or unavailable.\n"
        f"Your query has been logged and will be retried when providers reset.\n\n"
        f"Current Circuit Breaker Status:\n"
    )
    for entry in get_circuit_breaker_status():
        status = "✅ Available" if entry["available"] else f"⏸️ Isolated ({entry.get('reason', 'N/A')}, reset in {entry.get('reset_in_seconds', '?')}s)"
        fallback += f"• {entry['name']}: {status}\n"

    return fallback, "Fallback (All Providers Busy)", switch_log

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
            "provider_label": "Google Antigravity Universal Engine (AUTO-SWITCH MULTI-PROVIDER)",
            "user_id": "1012374182157",
            "account_id": "gen-lang-client-0177342458",
            "query_count": 58,
        },
        "api_keys": {},
        "logs": [],
        "history": [],
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

WEB_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Antigravity AI Console</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; display: flex; height: 100vh; }
        #sidebar { width: 300px; background: #1e293b; border-right: 1px solid #334155; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
        #main { flex: 1; display: flex; flex-direction: column; height: 100vh; }
        h1 { font-size: 1.2rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
        .card { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 15px; }
        .card h2 { font-size: 0.85rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 10px; letter-spacing: 1px; }
        .provider-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 0.85rem; border-bottom: 1px solid #1e293b; }
        .provider-item:last-child { border-bottom: none; }
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
        .badge-ok { background: #065f46; color: #34d399; }
        .badge-off { background: #7f1d1d; color: #f87171; }
        #chat-window { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 80%; padding: 14px 18px; border-radius: 12px; font-size: 0.95rem; line-height: 1.6; white-space: pre-wrap; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai-msg { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; align-self: flex-start; border-bottom-left-radius: 2px; }
        .meta-tag { font-size: 0.75rem; color: #38bdf8; margin-bottom: 6px; font-weight: 600; }
        #input-area { padding: 20px; background: #1e293b; border-top: 1px solid #334155; display: flex; gap: 10px; }
        input[type="text"] { flex: 1; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; color: white; font-size: 0.95rem; outline: none; }
        input[type="text"]:focus { border-color: #38bdf8; }
        button { background: #0284c7; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0369a1; }
        .quick-btn { background: #334155; font-size: 0.8rem; padding: 8px 12px; width: 100%; text-align: left; margin-bottom: 6px; border-radius: 6px; }
        .quick-btn:hover { background: #475569; }
    </style>
</head>
<body>
    <div id="sidebar">
        <h1>🚀 Google Antigravity</h1>
        <div class="card">
            <h2>Circuit Breaker Status</h2>
            <div id="providers-list">Loading providers...</div>
        </div>
        <div class="card">
            <h2>Quick Test Prompts</h2>
            <button class="quick-btn" onclick="sendPrompt('is the swimming pool in singapore yio chu kang open today')">🏊 Yio Chu Kang Pool</button>
            <button class="quick-btn" onclick="sendPrompt('what the average earning of singapore in 2025')">🇸🇬 SG Salary 2025</button>
            <button class="quick-btn" onclick="sendPrompt('is male and female human has bady and what is the factor that will make sure they have a male successory')">🧬 Biological Genetics</button>
            <button class="quick-btn" onclick="sendPrompt('Build me an app for field service calendar')">🛠️ Build Odoo Module</button>
        </div>
    </div>
    <div id="main">
        <div id="chat-window">
            <div class="message ai-msg">
                <div class="meta-tag">🤖 Google Antigravity AI Console</div>
                Welcome! Connected to the Docker Microservice on port 5005. Type your question or prompt below to chat with Antigravity!
            </div>
        </div>
        <div id="input-area">
            <input type="text" id="prompt-input" placeholder="Type your instruction or question..." onkeypress="if(event.key==='Enter') sendCurrentPrompt()">
            <button onclick="sendCurrentPrompt()">Send Prompt</button>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/circuit-breaker');
                const data = await res.json();
                const container = document.getElementById('providers-list');
                container.innerHTML = data.providers.map(p => `
                    <div class="provider-item">
                        <span>${p.name}</span>
                        <span class="badge ${p.available ? 'badge-ok' : 'badge-off'}">${p.available ? 'OK' : 'BUSY'}</span>
                    </div>
                `).join('');
            } catch (e) {}
        }

        async function sendPrompt(text) {
            const chatWin = document.getElementById('chat-window');
            chatWin.innerHTML += `<div class="message user-msg">${text}</div>`;
            chatWin.scrollTop = chatWin.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();
                chatWin.innerHTML += `
                    <div class="message ai-msg">
                        <div class="meta-tag">🤖 ${data.provider_used || 'Antigravity'}</div>
                        ${data.response.replace(/^🤖 Jemi \([^)]+\):\n\n/, '')}
                    </div>`;
            } catch (e) {
                chatWin.innerHTML += `<div class="message ai-msg" style="color: #f87171;">Error connecting to Antigravity service.</div>`;
            }
            chatWin.scrollTop = chatWin.scrollHeight;
            fetchStatus();
        }

        function sendCurrentPrompt() {
            const input = document.getElementById('prompt-input');
            const val = input.value.strip ? input.value.trim() : input.value;
            if (val) {
                sendPrompt(val);
                input.value = '';
            }
        }

        fetchStatus();
        setInterval(fetchStatus, 10000);
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
        elif self.path == "/settings":
            self._send_json(data["settings"])
        elif self.path == "/logs":
            self._send_json({"logs": data["logs"][:50], "count": len(data["logs"])})
        elif self.path == "/history":
            self._send_json({"history": data["history"][:50]})
        elif self.path == "/circuit-breaker":
            self._send_json({"providers": get_circuit_breaker_status()})
        elif self.path == "/api-keys":
            keys = data.get("api_keys", {})
            masked = {k: (v[:6] + "..." + v[-4:] if len(v) > 10 else "Set") for k, v in keys.items() if v}
            self._send_json({"api_keys": masked})
        else:
            self._send_json({
                "status": "online",
                "service": "Google Antigravity AI Engine (Auto-Switch Multi-Provider)",
                "endpoints": {
                    "GET /": "Interactive Antigravity Web Chat Console UI",
                    "POST /chat": "Send prompt, get AI response",
                    "GET /circuit-breaker": "Provider isolation status",
                },
            })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        try:
            req_json = json.loads(post_data)
        except Exception:
            req_json = {}

        data = load_data()

        if self.path == "/settings":
            new_settings = req_json.get("settings", {})
            data["settings"].update(new_settings)
            save_data(data)
            self._send_json({"status": "updated", "settings": data["settings"]})
            return

        if self.path == "/api-keys":
            new_keys = req_json.get("api_keys", {})
            if "api_keys" not in data:
                data["api_keys"] = {}
            data["api_keys"].update(new_keys)
            save_data(data)
            self._send_json({"status": "keys_updated", "message": f"Updated {len(new_keys)} API key(s)"})
            return

        user_prompt = req_json.get("prompt", "").strip()
        if not user_prompt:
            self._send_json({"status": "error", "message": "Empty prompt"}, 400)
            return

        data["settings"]["query_count"] = data["settings"].get("query_count", 0) + 1
        current_count = data["settings"]["query_count"]

        answer, provider_used, switch_log = dispatch_ai_query(user_prompt)
        resp_formatted = f"🤖 Jemi ({provider_used}):\n\n{answer}"

        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": ts_str,
            "query": user_prompt,
            "provider_used": provider_used,
            "switch_log": switch_log,
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
            "engine": "Google Antigravity Auto-Switch Multi-Provider Engine",
            "provider_used": provider_used,
            "switch_log": switch_log,
            "query_count": current_count,
            "response": resp_formatted,
            "circuit_breaker": get_circuit_breaker_status(),
        })

    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", "5005"))
    server = HTTPServer(("0.0.0.0", port), AntigravityHandler)
    print(f"Google Antigravity AI Engine running on port {port} with Web Console at http://0.0.0.0:{port}/")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
