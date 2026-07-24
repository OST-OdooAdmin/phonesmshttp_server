import json

code = open('server_sms_gateway.py', 'r', encoding='utf-8').read()
with open('update_payload.json', 'w', encoding='utf-8') as f:
    json.dump({'code': code}, f)

print("PAYLOAD_READY")
