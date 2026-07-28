import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    res = env["res.config.settings"].action_chat_with_gemini("what the best mobile plan in singapore")
    print("\n=================== LIVE TEST OUTPUT ===================")
    print(res.get("response", ""))
    print("========================================================\n")
