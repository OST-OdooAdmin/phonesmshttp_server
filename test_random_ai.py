import json
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    query = "what does a delivery manager in a ERP solution company do"
    res = env["res.config.settings"].action_chat_with_gemini(query)
    print("--- LIVE TEST RESULT FOR ERP DELIVERY MANAGER ROLE ---")
    print(json.dumps(res, indent=2))
