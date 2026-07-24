# -*- coding: utf-8 -*-
from odoo_studio_engine import OdooStudioEngine

def run_test():
    engine = OdooStudioEngine(
        module_name="Phone SMS Gateway",
        technical_name="phone_sms_gateway",
        description="Integrates Odoo SMS Platform with Android Cellular Gateway Server"
    )
    
    fields = [
        ("name", "Char", "Gateway Name"),
        ("server_url", "Char", "Gateway Base URL"),
        ("api_key", "Char", "API Secret Key"),
        ("active", "Boolean", "Active")
    ]
    
    manifest = engine.generate_manifest()
    model_code = engine.generate_model_code("phone.sms.gateway", "Phone SMS Gateway Config", fields)
    views_xml = engine.generate_views_xml("phone.sms.gateway", fields)
    security_csv = engine.generate_security_csv("phone.sms.gateway")
    
    print("=== MANIFEST GENERATED ===")
    print(manifest[:150] + "...")
    print("\n=== MODEL CODE GENERATED ===")
    print(model_code[:200] + "...")
    print("\n=== VIEWS XML GENERATED ===")
    print(views_xml[:200] + "...")
    print("\n=== SECURITY CSV GENERATED ===")
    print(security_csv)
    print("\nSTUDIO_SCAFFOLDING_VERIFIED_SUCCESS")

if __name__ == '__main__':
    run_test()
