import sqlite3
conn = sqlite3.connect('/root/sms_gateway.db')
rows = conn.execute('SELECT * FROM sms_queue ORDER BY id DESC LIMIT 10').fetchall()
print("DB RECORDS:")
for r in rows:
    print(r)
