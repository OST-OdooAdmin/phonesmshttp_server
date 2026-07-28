import json
import sys
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")

test_cases = [
    ("what the best mobile plan in singapore", ["simba", "eight", "giga", "singtel", "gomo"]),
    ("“砂拉越现代养猪业 —— 未来发展目标 根据相关发展规划，砂拉越目标是在2030年前： • 年产约86万头肉猪 • 产业产值目标约RM12.9亿” is this business good", ["pig", "swine", "export", "singapore", "12.9"]),
    ("where is the cheapest chicken rice in singapore", ["chicken rice", "hawker", "tian tian"]),
    ("yo jemi. what is the best way to travel in singape cheap", ["mrt", "buses", "tourist pass"]),
    ("what does a delivery manager in a ERP solution company do", ["delivery manager", "implementation", "governance"]),
    ("how much do odoo online subscription cost", ["pricing", "free plan", "standard plan"]),
    ("is the junk in sarawak kuching open at night?", ["sarawak", "the junk", "night"])
]

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    all_passed = True
    print("\n=================== STARTING COMPREHENSIVE LIVE TEST BATTERY (7 TESTS) ===================")
    for idx, (query, expected_keywords) in enumerate(test_cases, 1):
        res = env["res.config.settings"].action_chat_with_gemini(query)
        response_text = res.get("response", "").lower()
        passed = any(kw in response_text for kw in expected_keywords)
        status = "PASSED ✅" if passed else "FAILED ❌"
        if not passed:
            all_passed = False
        print(f"\n[Test {idx}/7] Query: '{query[:60]}...'")
        print(f"Status: {status}")
        print(f"Sample Output: {res.get('response', '')[:250]}...")
    print("\n=================== TEST BATTERY RESULT: " + ("ALL 7 PASSED 100% SUCCESS" if all_passed else "FAILED") + " ===================")
    if not all_passed:
        sys.exit(1)
