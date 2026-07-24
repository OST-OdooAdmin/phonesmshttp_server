package com.phonesms.server

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.gson.gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class PhoneDispatchPayload(
    val to: String,
    val message: String,
    val status: String,
    val detail: String
)

class MainActivity : ComponentActivity() {

    private var smsService: SmsForegroundService? = null
    private var isBound = false

    private val serverLogsState = mutableStateListOf<SmsLogRecord>()
    private val availableSimsState = mutableStateListOf<SimInfo>()
    private val selectedSubIdState = mutableStateOf<Int?>(null)
    private val logFetchStatusState = mutableStateOf("Tap Refresh to fetch server logs.")

    // Persistent Settings State
    private val serverUrlState = mutableStateOf("")
    private val apiKeyState = mutableStateOf("")
    private val isPollingEnabledState = mutableStateOf(false)

    private val httpClient by lazy {
        HttpClient(CIO) {
            install(ContentNegotiation) {
                gson()
            }
        }
    }

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(className: ComponentName, service: IBinder) {
            val binder = service as SmsForegroundService.LocalBinder
            smsService = binder.getService()
            isBound = true

            if (isPollingEnabledState.value && serverUrlState.value.isNotBlank()) {
                startPollingService()
            }
        }

        override fun onServiceDisconnected(arg0: ComponentName) {
            isBound = false
            smsService = null
        }
    }

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val smsGranted = permissions[Manifest.permission.SEND_SMS] ?: false
        if (smsGranted) {
            Toast.makeText(this, "SMS Permission Granted!", Toast.LENGTH_SHORT).show()
            reloadSimCards()
        } else {
            Toast.makeText(this, "SMS Permission is required to send SMS!", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        checkAndRequestPermissions()

        loadSettings()
        reloadSimCards()

        // Start & Bind Foreground Service
        val serviceIntent = Intent(this, SmsForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        bindService(serviceIntent, connection, Context.BIND_AUTO_CREATE)

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF4CAF50),
                    secondary = Color(0xFF2196F3),
                    background = Color(0xFF121212),
                    surface = Color(0xFF1E1E1E)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val scope = rememberCoroutineScope()

                    SmsGatewayApp(
                        serverLogs = serverLogsState,
                        logFetchStatus = logFetchStatusState.value,
                        availableSims = availableSimsState,
                        selectedSubId = selectedSubIdState.value,
                        serverUrl = serverUrlState.value,
                        apiKey = apiKeyState.value,
                        isPollingEnabled = isPollingEnabledState.value,
                        onSelectSim = { subId -> selectedSubIdState.value = subId },
                        onFetchServerLogs = {
                            scope.launch {
                                logFetchStatusState.value = "Fetching logs from server..."
                                val engine = PollingEngine(this@MainActivity) {}
                                val logs = engine.fetchServerLogs(serverUrlState.value, apiKeyState.value)
                                serverLogsState.clear()
                                serverLogsState.addAll(logs)
                                logFetchStatusState.value = if (logs.isNotEmpty()) {
                                    "Loaded ${logs.size} log records from server."
                                } else {
                                    "No logs returned from server (Check URL/Network connection)."
                                }
                            }
                        },
                        onSaveSettings = { url, key, enabled ->
                            serverUrlState.value = url
                            apiKeyState.value = key
                            isPollingEnabledState.value = enabled
                            saveSettings(url, key, enabled)

                            if (enabled) {
                                startPollingService()
                            } else {
                                stopPollingService()
                            }
                        },
                        onSendSms = { recipient, message ->
                            val words = getWordCount(message)
                            if (words > 500) {
                                Toast.makeText(this, "Error: Message exceeds 500 word limit ($words words)", Toast.LENGTH_LONG).show()
                                return@SmsGatewayApp
                            }
                            
                            val result = SmsSender.sendSms(this, recipient, message, targetSubId = selectedSubIdState.value)
                            val statusStr = if (result.success) "sent" else "failed"
                            Toast.makeText(this, result.message, Toast.LENGTH_LONG).show()
                            smsService?.addLog("Manual SMS -> $recipient [${if (result.success) "SUCCESS" else "FAILED"}]")

                            // Log directly to Server's /var/log/sms_gateway_activity.log
                            if (serverUrlState.value.isNotBlank()) {
                                scope.launch(Dispatchers.IO) {
                                    try {
                                        val logUrl = if (serverUrlState.value.endsWith("/")) "${serverUrlState.value}api/sms/log-dispatch" else "${serverUrlState.value}/api/sms/log-dispatch"
                                        httpClient.post(logUrl) {
                                            header("X-Api-Key", apiKeyState.value)
                                            contentType(ContentType.Application.Json)
                                            setBody(
                                                PhoneDispatchPayload(
                                                    to = recipient,
                                                    message = message,
                                                    status = statusStr,
                                                    detail = result.message
                                                )
                                            )
                                        }
                                        Log.d("MainActivity", "Posted dispatch log to server successfully.")
                                    } catch (e: Exception) {
                                        Log.e("MainActivity", "Failed to post dispatch log to server", e)
                                    }
                                }
                            }
                        }
                    )
                }
            }
        }
    }

    private fun startPollingService() {
        val intent = Intent(this, SmsForegroundService::class.java).apply {
            action = SmsForegroundService.ACTION_START_POLLING
            putExtra(SmsForegroundService.EXTRA_URL, serverUrlState.value)
            putExtra(SmsForegroundService.EXTRA_API_KEY, apiKeyState.value)
        }
        startService(intent)
    }

    private fun stopPollingService() {
        val intent = Intent(this, SmsForegroundService::class.java).apply {
            action = SmsForegroundService.ACTION_STOP_POLLING
        }
        startService(intent)
    }

    private fun loadSettings() {
        val prefs = getSharedPreferences("gateway_settings", Context.MODE_PRIVATE)
        serverUrlState.value = prefs.getString("server_url", "http://192.168.0.106:8069") ?: "http://192.168.0.106:8069"
        apiKeyState.value = prefs.getString("api_key", "secret_sms_key_123") ?: "secret_sms_key_123"
        isPollingEnabledState.value = prefs.getBoolean("polling_enabled", false)
    }

    private fun saveSettings(url: String, key: String, enabled: Boolean) {
        val prefs = getSharedPreferences("gateway_settings", Context.MODE_PRIVATE)
        prefs.edit()
            .putString("server_url", url)
            .putString("api_key", key)
            .putBoolean("polling_enabled", enabled)
            .apply()
    }

    private fun reloadSimCards() {
        availableSimsState.clear()
        val sims = SmsSender.getActiveSimCards(this)
        availableSimsState.addAll(sims)
        if (selectedSubIdState.value == null && sims.isNotEmpty()) {
            selectedSubIdState.value = sims[0].subId
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isBound) {
            unbindService(connection)
            isBound = false
        }
    }

    private fun checkAndRequestPermissions() {
        val neededPermissions = mutableListOf(Manifest.permission.SEND_SMS, Manifest.permission.READ_PHONE_STATE)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            neededPermissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val missing = neededPermissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missing.isNotEmpty()) {
            permissionLauncher.launch(missing.toTypedArray())
        }
    }

    private fun getWordCount(text: String): Int {
        if (text.isBlank()) return 0
        return text.trim().split("\\s+".toRegex()).size
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmsGatewayApp(
    serverLogs: List<SmsLogRecord>,
    logFetchStatus: String,
    availableSims: List<SimInfo>,
    selectedSubId: Int?,
    serverUrl: String,
    apiKey: String,
    isPollingEnabled: Boolean,
    onSelectSim: (Int) -> Unit,
    onFetchServerLogs: () -> Unit,
    onSaveSettings: (String, String, Boolean) -> Unit,
    onSendSms: (String, String) -> Unit
) {
    var recipientPhone by remember { mutableStateOf("") }
    var messageText by remember { mutableStateOf("") }
    var showSettingsDialog by remember { mutableStateOf(false) }

    val wordCount = remember(messageText) {
        if (messageText.isBlank()) 0 else messageText.trim().split("\\s+".toRegex()).size
    }
    val isWordCountExceeded = wordCount > 500

    var selectedTab by remember { mutableIntStateOf(0) }

    LaunchedEffect(selectedTab) {
        if (selectedTab == 1) {
            onFetchServerLogs()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // App Header with Settings Gear Icon
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "📱 Phone SMS Gateway App",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = if (isPollingEnabled) "🟢 Server Sync Active (1 min)" else "⚪ Offline / Standalone",
                    fontSize = 11.sp,
                    color = if (isPollingEnabled) Color(0xFF81C784) else Color.Gray
                )
            }
            IconButton(onClick = { showSettingsDialog = true }) {
                Icon(
                    imageVector = Icons.Default.Settings,
                    contentDescription = "Settings",
                    tint = Color.White
                )
            }
        }

        // Dual SIM Selector Bar if multiple SIM cards found
        if (availableSims.size > 1) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 10.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Send via:",
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = Color.Gray,
                        modifier = Modifier.padding(end = 8.dp)
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        availableSims.forEach { sim ->
                            val isSelected = selectedSubId == sim.subId
                            Box(
                                modifier = Modifier
                                    .background(
                                        color = if (isSelected) Color(0xFF4CAF50) else Color(0xFF333333),
                                        shape = RoundedCornerShape(16.dp)
                                    )
                                    .clickable { onSelectSim(sim.subId) }
                                    .padding(horizontal = 12.dp, vertical = 6.dp)
                            ) {
                                Text(
                                    text = "SIM ${sim.slotIndex}: ${sim.carrierName}",
                                    color = Color.White,
                                    fontSize = 12.sp,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                                )
                            }
                        }
                    }
                }
            }
        }

        // Navigation Tabs (Send SMS vs View Server Logs)
        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("✉️ Send SMS") }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("📋 Server Logs (${serverLogs.size})") }
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (selectedTab == 0) {
            // TAB 1: SEND SMS FORM
            Column(modifier = Modifier.fillMaxWidth()) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "Recipient Phone Number", fontWeight = FontWeight.SemiBold)
                    Text(text = "Format: +65xxxxxxx", fontSize = 11.sp, color = Color.Gray)
                }
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = recipientPhone,
                    onValueChange = { recipientPhone = it },
                    placeholder = { Text("+6591234567 or 91234567") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "Message Content", fontWeight = FontWeight.SemiBold)
                    
                    TextButton(
                        onClick = {
                            val timestampStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
                            messageText = "Test SMS from Android Gateway [$timestampStr]"
                        },
                        contentPadding = PaddingValues(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text("🧪 Fill Test Msg", fontSize = 11.sp, color = Color(0xFF64B5F6))
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = messageText,
                    onValueChange = { messageText = it },
                    placeholder = { Text("Type message here (Max 500 words)...") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(140.dp),
                    isError = isWordCountExceeded
                )

                if (isWordCountExceeded) {
                    Text(
                        text = "⚠️ Message exceeds maximum 500 words limit!",
                        color = Color.Red,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = {
                        if (recipientPhone.isNotBlank() && messageText.isNotBlank()) {
                            val cleanTarget = if (!recipientPhone.startsWith("+") && recipientPhone.length == 8) {
                                "+65$recipientPhone"
                            } else {
                                recipientPhone
                            }
                            onSendSms(cleanTarget, messageText)
                            messageText = ""
                        }
                    },
                    enabled = recipientPhone.isNotBlank() && messageText.isNotBlank() && !isWordCountExceeded,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("🚀 Send SMS Message", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
        } else {
            // TAB 2: SERVER LOGS VIEW (FETCHED DIRECTLY FROM SERVER)
            Column(modifier = Modifier.fillMaxWidth().weight(1f)) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(10.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = "Central Server Logs", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                            Text(text = logFetchStatus, fontSize = 11.sp, color = Color.Gray)
                        }
                        IconButton(onClick = onFetchServerLogs) {
                            Icon(imageVector = Icons.Default.Refresh, contentDescription = "Refresh Logs", tint = Color(0xFF64B5F6))
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                if (serverLogs.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color(0xFF1E1E1E), shape = RoundedCornerShape(8.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(text = "No server logs loaded yet.", color = Color.Gray)
                            Spacer(modifier = Modifier.height(8.dp))
                            Button(onClick = onFetchServerLogs) {
                                Text("🔄 Fetch Live Logs From Server")
                            }
                        }
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(serverLogs) { log ->
                            SmsLogCard(log)
                        }
                    }
                }
            }
        }
    }

    // Settings Dialog Modal
    if (showSettingsDialog) {
        var tempUrl by remember { mutableStateOf(serverUrl) }
        var tempKey by remember { mutableStateOf(apiKey) }
        var tempEnabled by remember { mutableStateOf(isPollingEnabled) }

        AlertDialog(
            onDismissRequest = { showSettingsDialog = false },
            title = { Text("⚙️ Local Server Settings", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(text = "Local Server Base URL:", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    OutlinedTextField(
                        value = tempUrl,
                        onValueChange = { tempUrl = it },
                        placeholder = { Text("http://192.168.0.106:8069") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Text(text = "API Key:", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    OutlinedTextField(
                        value = tempKey,
                        onValueChange = { tempKey = it },
                        placeholder = { Text("secret_sms_key_123") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Text(text = "Polling Interval: 1 minute (60s JSON format)", fontSize = 11.sp, color = Color.Gray)

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "Enable Server Sync", fontSize = 13.sp)
                        Switch(
                            checked = tempEnabled,
                            onCheckedChange = { tempEnabled = it }
                        )
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        onSaveSettings(tempUrl.trim(), tempKey.trim(), tempEnabled)
                        showSettingsDialog = false
                    }
                ) {
                    Text("Save Settings")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSettingsDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun SmsLogCard(log: SmsLogRecord) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (log.status.startsWith("SUCCESS") || log.status.lowercase() == "sent") Color(0xFF1B2E1B) else (if (log.status.uppercase() == "QUEUED") Color(0xFF332B1B) else Color(0xFF331B1B))
        )
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "To: ${log.recipient}",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = Color.White
                )
                Text(
                    text = log.status,
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    color = if (log.status.startsWith("SUCCESS") || log.status.lowercase() == "sent") Color(0xFF81C784) else (if (log.status.uppercase() == "QUEUED") Color(0xFFFFB74D) else Color(0xFFE57373))
                )
            }
            Spacer(modifier = Modifier.height(2.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(text = "Time: ${log.timestamp}", fontSize = 11.sp, color = Color.Gray)
                Text(text = "${log.wordCount} words", fontSize = 11.sp, color = Color.Gray)
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = log.message,
                fontSize = 13.sp,
                color = Color(0xFFE0E0E0),
                fontFamily = FontFamily.SansSerif
            )
        }
    }
}
