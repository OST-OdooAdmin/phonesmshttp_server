@echo off
echo ===================================================
echo   Deploying Stage 1 SMS HTTP Gateway App to Phone
echo ===================================================

set ADB="C:\Users\MLAU\AppData\Local\Android\Sdk\platform-tools\adb.exe"

if not exist %ADB% (
    set ADB=adb
)

%ADB% devices
echo.
echo Installing Stage 1 Phone SMS Gateway App (com.phonesms.server)...
%ADB% install -r "C:\Users\MLAU\.gemini\antigravity\scratch\phonesmshttp_server\android_app\app\build\outputs\apk\debug\app-debug.apk"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Stage 1 SMS HTTP Gateway installed! Launching app on phone...
    %ADB% shell am start -n com.phonesms.server/.MainActivity
) else (
    echo.
    echo ERROR: Could not push to device via ADB. Check USB connection.
)
