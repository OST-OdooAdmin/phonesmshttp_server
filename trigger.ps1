$body = '{"to":"+6596780253","message":"[ONE-TIME REQUEST TRIGGER] Test message at 2026-07-24 14:18:14"}'
Invoke-RestMethod -Uri 'http://115.135.158.84:2222/queue-sms' -Method POST -ContentType 'application/json' -Body $body
