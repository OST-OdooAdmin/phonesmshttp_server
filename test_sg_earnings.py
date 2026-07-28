import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")

user_question = "what the average earning of singapore in 2025"

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    res = env["res.config.settings"].action_chat_with_gemini(user_question)
    print("=================== JEMI LIVE RESPONSE POSTED TO ODOO CHATTER ===================")
    print(res.get("response", ""))
    print("=================================================================================")
