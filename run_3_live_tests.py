import json
import sys
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")

test_questions = [
    ("what the best mobile plan in singapore", ["eight", "simba", "giga", "gomo", "singtel"]),
    ("“砂拉越现代养猪业 —— 未来发展目标 年产约86万头肉猪” is this business good", ["pig", "swine", "export", "12.9", "singapore"]),
    ("where is the cheapest chicken rice in singapore", ["chicken rice", "hawker", "tian tian", "maxwell"])
]

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_passed = True
    print("\n=================== STARTING 3 LIVE TEST QUESTIONS RUN ===================")
    for idx, (query, expected_keywords) in enumerate(test_questions, 1):
        res = env["res.config.settings"].action_chat_with_gemini(query)
        response_text = res.get("response", "").lower()
        passed = any(kw in response_text for kw in expected_keywords)
        status = "PASSED ✅" if passed else "FAILED ❌"
        if not passed:
            all_passed = False
        print(f"\n----------------------------------------------------------------------")
        print(f"LIVE TEST #{idx}: Question: '{query}'")
        print(f"Status: {status}")
        print(f"Log Info: {res.get('log_info', '')}")
        print(f"Response Preview:\n{res.get('response', '')}")
        print(f"----------------------------------------------------------------------")
    
    print("\n=================== 3 LIVE TESTS RESULT: " + ("ALL 3 PASSED 100% SUCCESS" if all_passed else "FAILED") + " ===================")
    if not all_passed:
        sys.exit(1)
