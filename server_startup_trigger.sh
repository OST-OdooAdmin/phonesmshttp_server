#!/bin/bash
# Server Startup Trigger Script
# Runs automatically whenever the server or SMS Gateway service starts up

RECIPIENT="+6596780253"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
MESSAGE="[SERVER STARTUP TRIGGER] Gateway Online at ${TIMESTAMP}"

# Add startup message task to SQLite database & log file
python3 /root/server_sms_gateway.py add "${RECIPIENT}" "${MESSAGE}"

echo "[${TIMESTAMP}] 🚀 Executed Server Startup Trigger for ${RECIPIENT}" >> /var/log/sms_gateway_activity.log
