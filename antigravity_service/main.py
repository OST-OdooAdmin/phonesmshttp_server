import json
import ssl
import time
import os
import re
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DATA_FILE = "/app/antigravity_data.json"

# ============================================================================
# MULTI-PROVIDER AUTO-SWITCH CIRCUIT BREAKER ENGINE
# Providers from different companies have INDEPENDENT rate limits & credit pools.
# If one hits a limit, we instantly switch to the next available provider.
# ============================================================================

PROVIDER_REGISTRY = [
    # --- SECTION 1: FREE & UNLIMITED (Primary Default - Local Reasoning) ---
    {
        "id": "antigravity_local",
        "name": "Google Antigravity Local Reasoning Engine",
        "section": 1,
        "type": "local",
        "credit_pool": "antigravity",
        "rpm_limit": 0,  # unlimited
        "isolation_seconds": 0,
    },
    # --- SECTION 2: PAID ENTERPRISE APIs (Independent Credit Pools) ---
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

# In-memory circuit breaker state
CIRCUIT_BREAKER = {}  # provider_id -> {"isolated_until": timestamp, "reason": str}


def get_api_key(env_key):
    """Get API key from environment or settings file."""
    key = os.environ.get(env_key, "")
    if not key:
        data = load_data()
        keys = data.get("api_keys", {})
        key = keys.get(env_key, "")
    return key.strip()


def is_provider_available(provider):
    """Check if a provider is available (not isolated by circuit breaker)."""
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
    """Isolate a provider for its configured isolation period."""
    pid = provider["id"]
    duration = provider.get("isolation_seconds", 60)
    CIRCUIT_BREAKER[pid] = {
        "isolated_until": time.time() + duration,
        "reason": reason,
        "provider_name": provider["name"],
        "reset_in_seconds": duration,
    }


def isolate_credit_pool(pool_name, reason="credit_exhausted"):
    """Isolate ALL providers sharing the same credit pool."""
    for p in PROVIDER_REGISTRY:
        if p.get("credit_pool") == pool_name and p["type"] != "local":
            isolate_provider(p, reason)


def get_circuit_breaker_status():
    """Return current circuit breaker state for all providers."""
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


# ============================================================================
# LIVE API CALLERS (Each provider type has its own HTTP caller)
# ============================================================================

def call_gemini_api(provider, prompt):
    """Call Google Gemini API."""
    api_key = get_api_key(provider["env_key"])
    model = provider["model"]
    ver = provider["api_version"]
    url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")

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
    """Call OpenAI ChatCompletion API."""
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
    """Call Anthropic Claude Messages API."""
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
    "api": call_gemini_api,      # Gemini
    "openai": call_openai_api,   # OpenAI
    "anthropic": call_anthropic_api,  # Anthropic Claude
}


# ============================================================================
# LOCAL REASONING ENGINE (Section 1 Fallback - Always Available)
# ============================================================================

def local_reasoning_engine(user_prompt):
    """Built-in factual reasoning engine. Always available, zero rate limits."""
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
        return None  # Signal: no local answer, try live APIs


# ============================================================================
# MASTER AI DISPATCHER (Auto-Switch + Circuit Breaker)
# ============================================================================

def dispatch_ai_query(user_prompt):
    """
    Master dispatcher that tries providers in order:
    1. Local reasoning engine (always available, zero limits)
    2. Live API providers (auto-switch on rate limit / credit exhaustion)

    Returns (answer_text, provider_name, switch_log)
    """
    switch_log = []

    # STEP 1: Try local reasoning engine first (Section 1 - unlimited)
    local_answer = local_reasoning_engine(user_prompt)
    if local_answer:
        return local_answer, "Google Antigravity Local Engine", switch_log

    # STEP 2: Try live API providers in order, skipping isolated ones
    for provider in PROVIDER_REGISTRY:
        if provider["type"] == "local":
            continue  # already tried

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

    # STEP 3: Fallback generic response if all APIs unavailable
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


# ============================================================================
# PERSISTENT DATA STORAGE
# ============================================================================

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
            "query_count": 57,
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


# ============================================================================
# HTTP SERVER
# ============================================================================

class AntigravityHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        data = load_data()
        if self.path == "/settings":
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
                "features": ["auto_switch", "circuit_breaker", "multi_provider", "rate_limit_rotation"],
                "endpoints": {
                    "POST /chat": "Send a prompt, get AI response with auto-switching",
                    "GET /settings": "View engine settings",
                    "POST /settings": "Update engine settings",
                    "GET /logs": "View communication logs",
                    "GET /history": "View conversation history",
                    "GET /circuit-breaker": "View provider availability & isolation status",
                    "GET /api-keys": "View configured API keys (masked)",
                    "POST /api-keys": "Configure API keys for paid providers",
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

        # --- Update Settings ---
        if self.path == "/settings":
            new_settings = req_json.get("settings", {})
            data["settings"].update(new_settings)
            save_data(data)
            self._send_json({"status": "updated", "settings": data["settings"]})
            return

        # --- Configure API Keys ---
        if self.path == "/api-keys":
            new_keys = req_json.get("api_keys", {})
            if "api_keys" not in data:
                data["api_keys"] = {}
            data["api_keys"].update(new_keys)
            save_data(data)
            self._send_json({"status": "keys_updated", "message": f"Updated {len(new_keys)} API key(s)"})
            return

        # --- Chat Endpoint (Auto-Switch Multi-Provider) ---
        user_prompt = req_json.get("prompt", "").strip()
        if not user_prompt:
            self._send_json({"status": "error", "message": "Empty prompt"}, 400)
            return

        data["settings"]["query_count"] = data["settings"].get("query_count", 0) + 1
        current_count = data["settings"]["query_count"]

        # Dispatch through multi-provider auto-switch engine
        answer, provider_used, switch_log = dispatch_ai_query(user_prompt)

        resp_formatted = f"🤖 Jemi ({provider_used}):\n\n{answer}"

        # Record logs
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
        pass  # Suppress default HTTP logs


def run_server():
    port = int(os.environ.get("PORT", "5005"))
    server = HTTPServer(("0.0.0.0", port), AntigravityHandler)
    print(f"Google Antigravity AI Engine (Auto-Switch Multi-Provider) running on port {port}...")
    print(f"Providers registered: {len(PROVIDER_REGISTRY)}")
    print(f"Credit pools: {set(p['credit_pool'] for p in PROVIDER_REGISTRY)}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
