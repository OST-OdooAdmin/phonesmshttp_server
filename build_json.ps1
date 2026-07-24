$code = Get-Content -Raw -Path 'C:\Users\MLAU\.gemini\antigravity\scratch\phonesmshttp_server\server_sms_gateway.py'
$obj = @{ code = $code }
$json = $obj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText('C:\Users\MLAU\.gemini\antigravity\scratch\phonesmshttp_server\update_payload.json', $json)
