# Phone SMS HTTP Server & Odoo Integration (`phonesmshttp_server`)

`phonesmshttp_server` turns an Android smartphone into an automated **SMS Gateway** for server applications (such as Odoo ERP). It enables sending SMS notifications, two-factor authentication codes, and customer updates directly through your phone's SIM card.

---

## Architecture Overview

```
+-------------------------------------------------------------------+
|                        Odoo ERP / Server                          |
|  (Custom Odoo Module: phone_sms_gateway)                          |
+-------------------------------------------------------------------+
           |                                             ^
           | Option 1: Direct HTTP POST                  | Option 2: App Polls
           | http://<phone_ip>:8080/send-sms              | /api/sms/pending
           v                                             |
+-------------------------------------------------------------------+
|                     Android Phone Gateway                         |
|  - Embedded Ktor HTTP Server (:8080)                              |
|  - Polling Client Engine (4G/5G mobile data compatible)           |
|  - Foreground Service (Runs continuously when screen is locked)   |
|  - Android SmsManager (Dispatches SMS via SIM card)               |
+-------------------------------------------------------------------+
           |
           v
+-------------------------------------------------------------------+
|                      Cellular Network                             |
|  Sends SMS to recipient phone number                             |
+-------------------------------------------------------------------+
```

---

## Project Structure

```
phonesmshttp_server/
├── README.md                           # Documentation & Setup Guide
├── .gitignore                          # Git exclusions for Android & Odoo
├── android_app/                        # Android Phone Gateway App (Kotlin / Jetpack Compose)
│   ├── app/
│   │   ├── build.gradle.kts            # App build script & dependencies
│   │   └── src/main/
│   │       ├── AndroidManifest.xml     # Permissions & Service definitions
│   │       └── java/com/phonesms/server/
│   │           ├── MainActivity.kt     # Compose UI (Control panel & log display)
│   │           ├── SmsForegroundService.kt # Background service keeper
│   │           ├── HttpServerEngine.kt # Ktor HTTP server listener (:8080)
│   │           ├── PollingEngine.kt    # Odoo polling client
│   │           └── SmsSender.kt        # Android SmsManager dispatcher
│   ├── build.gradle.kts                # Root project build file
│   └── settings.gradle.kts             # Gradle project settings
└── odoo_module/                        # Odoo ERP SMS Gateway Module
    └── phone_sms_gateway/
        ├── __manifest__.py             # Odoo module metadata
        ├── __init__.py
        ├── controllers/
        │   └── main.py                 # Odoo HTTP API (/api/sms/pending & /api/sms/status)
        ├── models/
        │   └── sms_gateway.py          # Odoo SMS Queue & Log model
        └── views/
            └── sms_gateway_view.xml    # Odoo UI admin view
```

---

## 🚀 How to Connect to GitHub (Dual-AI Collaboration Guide)

Follow these steps to link this project repository to GitHub so that another AI coding assistant on another device or account can access and collaborate on this project:

### Step 1: Create a Repository on GitHub
1. Go to [GitHub.com](https://github.com) and sign in.
2. Click **New Repository** (`+` icon at the top right).
3. Name the repository: `phonesmshttp_server`.
4. Set visibility to **Public** or **Private** (Private recommended).
5. **Do NOT check** "Add a README file", ".gitignore", or "Choose a license" (since we already created them locally).
6. Click **Create repository**.

### Step 2: Push Local Code to GitHub
Open your terminal inside this project directory (`C:\Users\MLAU\.gemini\antigravity\scratch\phonesmshttp_server`) and run:

```bash
# Set your main branch name to main
git branch -M main

# Add your GitHub repository as the remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/phonesmshttp_server.git

# Push code to GitHub
git push -u origin main
```

### Step 3: Access from Your Second AI Coding Assistant Account
On your second machine/account:
1. Open your second AI coding tool (e.g. Antigravity, Cursor, GitHub Copilot, VSCode, etc.).
2. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/phonesmshttp_server.git
   ```
3. Open the folder in the second AI assistant tool.
4. **Collaborate seamlessly**: Both AI assistants can commit, pull (`git pull`), and push changes to work on the Android app or Odoo module simultaneously!

---

## Quick API Reference

### 1. Embedded Phone HTTP Server (Local Wi-Fi)
* **Endpoint**: `POST http://<PHONE_IP>:8080/send-sms`
* **Headers**: `Content-Type: application/json`
* **Body**:
  ```json
  {
    "to": "+1234567890",
    "message": "Hello from Odoo server!"
  }
  ```
* **Response**:
  ```json
  {
    "status": "success",
    "message_id": "sms_1721458900"
  }
  ```

### 2. Odoo Polling Endpoint (Remote / 4G/5G)
* **Endpoint**: `GET https://<YOUR_ODOO_SERVER>/api/sms/pending`
* **Headers**: `X-Api-Key: <YOUR_SECRET_KEY>`
* **Response**:
  ```json
  {
    "pending": [
      {
        "id": 101,
        "to": "+1234567890",
        "message": "Your Odoo invoice #INV0042 is ready."
      }
    ]
  }
  ```
