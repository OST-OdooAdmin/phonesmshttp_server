import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(["--db_host=db", "--db_user=odoo", "--db_password=odoo", "-d", "DreamHRsolution"])
registry = odoo.registry("DreamHRsolution")

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env['ir.config_parameter'].sudo()
    ICP.set_param('odoo_studio_builder.ai_provider', 'antigravity')
    ICP.set_param('odoo_studio_builder.jemi_user_id', '1012374182157')
    ICP.set_param('odoo_studio_builder.jemi_account_id', 'gen-lang-client-0177342458')
    cr.commit()
    print("✅ PERMANENT ACCOUNT SETTINGS UPDATED ON SERVER DATABASE 'DreamHRsolution':")
    print("  • AI Engine Provider: SECTION 1 [PRIMARY DEFAULT]: Google Antigravity Universal Engine")
    print("  • Account User ID: 1012374182157")
    print("  • Organization ID: gen-lang-client-0177342458")
