package com.phonesms.server

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
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
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.gson.gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

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
    private val logFetchStatusState = mutableStateOf("Server sync running.")

    // Live 1-Minute Visual Countdown State
    private val countdownSecondsState = mutableStateOf(60)

    // Persistent Settings State
    private val serverUrlState = mutableStateOf("")
    private val apiKeyState = mutableStateOf("")
    private val isPollingEnabledState = mutableStateOf(true)

    private val httpClient by lazy {
        HttpClient(CIO) {
            install(ContentNegotiation) {
                gson()
            }
            install(HttpTimeout) {
                requestTimeoutMillis = 5000
                connectTimeoutMillis = 4000
                socketTimeoutMillis = 5000
            }
        }
    }

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(className: ComponentName, service: IBinder) {
            val binder = service as SmsForegroundService.LocalBinder
            smsService = binder.getService()
            isBound = true

            if (serverUrlState.value.isNotBlank() && isPollingEnabledState.value) {
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

        // Start & Bind Foreground Service Safely
        try {
            val serviceIntent = Intent(this, SmsForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
            bindService(serviceIntent, connection, Context.BIND_AUTO_CREATE)
        } catch (e: Exception) {
            Log.e("MainActivity", "Failed to start/bind service: ${e.message}")
        }

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

                    fun autoFetchLogs() {
                        scope.launch(Dispatchers.IO) {
                            try {
                                if (serverUrlState.value.isBlank()) return@launch
                                val engine = PollingEngine(this@MainActivity) {}
                                val logs = engine.fetchServerLogs(serverUrlState.value, apiKeyState.value)
                                launch(Dispatchers.Main) {
                                    serverLogsState.clear()
                                    serverLogsState.addAll(logs)
                                    logFetchStatusState.value = if (logs.isNotEmpty()) {
                                        "Synced ${logs.size} log records from server."
                                    } else {
                                        "No server logs found."
                                    }
                                }
                            } catch (e: Exception) {
                                Log.e("MainActivity", "autoFetchLogs error: ${e.message}")
                            }
                        }
                    }

                    // Live 1-Minute (60s) Countdown Loop
                    LaunchedEffect(isPollingEnabledState.value) {
                        if (isPollingEnabledState.value) {
                            while (true) {
                                autoFetchLogs()
                                countdownSecondsState.value = 60
                                for (i in 60 downTo 1) {
                                    countdownSecondsState.value = i
                                    delay(1000L)
                                }
                            }
                        } else {
                            countdownSecondsState.value = 0
                        }
                    }

                    SmsGatewayApp(
                        serverLogs = serverLogsState,
                        logFetchStatus = logFetchStatusState.value,
                        availableSims = availableSimsState,
                        selectedSubId = selectedSubIdState.value,
                        serverUrl = serverUrlState.value,
                        apiKey = apiKeyState.value,
                        isPollingEnabled = isPollingEnabledState.value,
                        countdownSeconds = countdownSecondsState.value,
                        onSelectSim = { subId -> selectedSubIdState.value = subId },
                        onTabChanged = { tab ->
                            if (tab == 1) {
                                autoFetchLogs()
                            }
                        },
                        onSaveSettings = { url, key, enabled ->
                            serverUrlState.value = url.trim()
                            apiKeyState.value = key.trim()
                            isPollingEnabledState.value = enabled
                            saveSettings(url.trim(), key.trim(), enabled)

                            stopPollingService()
                            if (enabled) {
                                startPollingService()
                            }
                            autoFetchLogs()
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
                                        launch(Dispatchers.Main) {
                                            autoFetchLogs()
                                        }
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

    override fun onResume() {
        super.onResume()
        if (serverUrlState.value.isNotBlank() && isPollingEnabledState.value) {
            try {
                startPollingService()
            } catch (e: Exception) {
                Log.e("MainActivity", "onResume error: ${e.message}")
            }
        }
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.SEND_SMS)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.READ_PHONE_STATE)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        if (permissionsToRequest.isNotEmpty()) {
            permissionLauncher.launch(permissionsToRequest.toTypedArray())
        }
    }

    private fun reloadSimCards() {
        try {
            val sims = SmsSender.getActiveSimCards(this)
            availableSimsState.clear()
            availableSimsState.addAll(sims)
            if (selectedSubIdState.value == null && sims.isNotEmpty()) {
                selectedSubIdState.value = sims.first().subId
            }
        } catch (e: Exception) {
            Log.e("MainActivity", "reloadSimCards exception: ${e.message}")
        }
    }

    private fun startPollingService() {
        try {
            val intent = Intent(this, SmsForegroundService::class.java).apply {
                action = SmsForegroundService.ACTION_START_POLLING
                putExtra(SmsForegroundService.EXTRA_URL, serverUrlState.value)
                putExtra(SmsForegroundService.EXTRA_API_KEY, apiKeyState.value)
            }
            startService(intent)
        } catch (e: Exception) {
            Log.e("MainActivity", "startPollingService error: ${e.message}")
        }
    }

    private fun stopPollingService() {
        try {
            val intent = Intent(this, SmsForegroundService::class.java).apply {
                action = SmsForegroundService.ACTION_STOP_POLLING
            }
            startService(intent)
        } catch (e: Exception) {
            Log.e("MainActivity", "stopPollingService error: ${e.message}")
        }
    }

    private fun loadSettings() {
        try {
            val prefs = getSharedPreferences("gateway_settings", Context.MODE_PRIVATE)
            serverUrlState.value = prefs.getString("server_url", "http://115.135.158.84:22") ?: "http://115.135.158.84:22"
            apiKeyState.value = prefs.getString("api_key", "secret_sms_key_123") ?: "secret_sms_key_123"
            isPollingEnabledState.value = prefs.getBoolean("polling_enabled", true)
        } catch (e: Exception) {
            Log.e("MainActivity", "loadSettings error: ${e.message}")
            serverUrlState.value = "http://115.135.158.84:22"
            apiKeyState.value = "secret_sms_key_123"
            isPollingEnabledState.value = true
        }
    }

    private fun saveSettings(url: String, key: String, enabled: Boolean) {
        try {
            val prefs = getSharedPreferences("gateway_settings", Context.MODE_PRIVATE)
            prefs.edit()
                .putString("server_url", url)
                .putString("api_key", key)
                .putBoolean("polling_enabled", enabled)
                .apply()
        } catch (e: Exception) {
            Log.e("MainActivity", "saveSettings error: ${e.message}")
        }
    }

    private fun getWordCount(text: String): Int {
        if (text.isBlank()) return 0
        return text.trim().split("\\s+".toRegex()).size
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isBound) {
            try {
                unbindService(connection)
            } catch (e: Exception) {
                Log.e("MainActivity", "unbindService exception: ${e.message}")
            }
            isBound = false
        }
    }
}

@Composable
fun SmsGatewayApp(
    serverLogs: List<SmsLogRecord>,
    logFetchStatus: String,
    availableSims: List<SimInfo>,
    selectedSubId: Int?,
    serverUrl: String,
    apiKey: String,
    isPollingEnabled: Boolean,
    countdownSeconds: Int,
    onSelectSim: (Int) -> Unit,
    onTabChanged: (Int) -> Unit,
    onSaveSettings: (String, String, Boolean) -> Unit,
    onSendSms: (String, String) -> Unit
) {
    var selectedTab by remember { mutableStateOf(0) }

    Column(modifier = Modifier.fillMaxSize()) {
        // Banner with live 1-minute countdown timer
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            colors = CardDefaults.cardColors(
                containerColor = if (isPollingEnabled) Color(0xFF1E3A29) else Color(0xFF333333)
            )
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = if (isPollingEnabled) "🟢 Server Sync Active (Every 1 Min)" else "⚪ Server Sync Off",
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        fontSize = 14.sp
                    )
                    Text(
                        text = if (isPollingEnabled) "Next Server Fetch in: ${countdownSeconds}s" else "Enable sync in Settings tab",
                        color = if (isPollingEnabled) Color(0xFF81C784) else Color.Gray,
                        fontSize = 12.sp
                    )
                }

                if (isPollingEnabled) {
                    CircularProgressIndicator(
                        progress = { (60 - countdownSeconds) / 60f },
                        modifier = Modifier.size(28.dp),
                        color = Color(0xFF4CAF50),
                        strokeWidth = 3.dp
                    )
                }
            }
        }

        TabRow(
            selectedTabIndex = selectedTab,
            containerColor = MaterialTheme.colorScheme.surface,
            contentColor = MaterialTheme.colorScheme.primary
        ) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0; onTabChanged(0) },
                text = { Text("Send SMS", fontWeight = FontWeight.Bold) }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1; onTabChanged(1) },
                text = { Text("Server Logs", fontWeight = FontWeight.Bold) }
            )
            Tab(
                selected = selectedTab == 2,
                onClick = { selectedTab = 2; onTabChanged(2) },
                text = { Text("Settings", fontWeight = FontWeight.Bold) }
            )
        }

        when (selectedTab) {
            0 -> SendSmsScreen(availableSims, selectedSubId, onSelectSim, onSendSms)
            1 -> ServerLogsScreen(serverLogs, logFetchStatus, onRefresh = { onTabChanged(1) })
            2 -> SettingsScreen(serverUrl, apiKey, isPollingEnabled, onSaveSettings)
        }
    }
}

@Composable
fun SendSmsScreen(
    sims: List<SimInfo>,
    selectedSubId: Int?,
    onSelectSim: (Int) -> Unit,
    onSendSms: (String, String) -> Unit
) {
    var recipient by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text("Outbound Cellular SMS Dispatcher", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color.White)
        Spacer(modifier = Modifier.height(12.dp))

        if (sims.isNotEmpty()) {
            Text("Select SIM Card Slot:", fontSize = 14.sp, color = Color.LightGray)
            Row(modifier = Modifier.padding(vertical = 8.dp)) {
                sims.forEach { sim ->
                    FilterChip(
                        selected = (selectedSubId == sim.subId),
                        onClick = { onSelectSim(sim.subId) },
                        label = { Text("SIM ${sim.slotIndex} (${sim.carrierName})") },
                        modifier = Modifier.padding(end = 8.dp)
                    )
                }
            }
        }

        OutlinedTextField(
            value = recipient,
            onValueChange = { recipient = it },
            label = { Text("Recipient Phone Number (e.g. +6596780253)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = message,
            onValueChange = { message = it },
            label = { Text("SMS Message Body") },
            modifier = Modifier
                .fillMaxWidth()
                .height(140.dp)
        )
        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = {
                if (recipient.isNotBlank() && message.isNotBlank()) {
                    onSendSms(recipient.trim(), message.trim())
                    message = ""
                }
            },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4CAF50))
        ) {
            Text("DISPATCH CELLULAR SMS NOW", color = Color.White, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun ServerLogsScreen(
    logs: List<SmsLogRecord>,
    logFetchStatus: String,
    onRefresh: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Central Gateway Logs (3 Months)", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color.White)
            IconButton(onClick = onRefresh) {
                Text("🔄", fontSize = 18.sp)
            }
        }

        Text(logFetchStatus, fontSize = 12.sp, color = Color.Gray)
        Spacer(modifier = Modifier.height(8.dp))

        if (logs.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No server logs found.", color = Color.Gray)
            }
        } else {
            LazyColumn(modifier = Modifier.fillMaxSize()) {
                items(logs) { log ->
                    val statusColor = when (log.status) {
                        "SUCCESS" -> Color(0xFF4CAF50)
                        "FAILED" -> Color(0xFFF44336)
                        else -> Color(0xFFFF9800)
                    }

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E))
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(log.recipient, fontWeight = FontWeight.Bold, color = Color.White)
                                Text(log.status, color = statusColor, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(log.message, color = Color.LightGray, fontSize = 14.sp)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text("${log.timestamp} • ${log.wordCount} words", color = Color.Gray, fontSize = 11.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SettingsScreen(
    currentUrl: String,
    currentKey: String,
    currentEnabled: Boolean,
    onSave: (String, String, Boolean) -> Unit
) {
    var urlInput by remember { mutableStateOf(currentUrl) }
    var keyInput by remember { mutableStateOf(currentKey) }
    var enabledInput by remember { mutableStateOf(currentEnabled) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text("SMS Gateway Settings", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = urlInput,
            onValueChange = { urlInput = it },
            label = { Text("Server Gateway URL (e.g. http://115.135.158.84:22)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = keyInput,
            onValueChange = { keyInput = it },
            label = { Text("API Security Key") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text("Enable Background Server Sync", color = Color.White)
            Switch(
                checked = enabledInput,
                onCheckedChange = { enabledInput = it }
            )
        }
        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                onSave(urlInput, keyInput, enabledInput)
            },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2196F3))
        ) {
            Text("SAVE GATEWAY SETTINGS", color = Color.White, fontWeight = FontWeight.Bold)
        }
    }
}
