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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import java.net.NetworkInterface
import java.util.Collections

class MainActivity : ComponentActivity() {

    private var smsService: SmsForegroundService? = null
    private var isBound = false

    private val isServerRunningState = mutableStateOf(false)
    private val savedLogsState = mutableStateListOf<SmsLogRecord>()

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(className: ComponentName, service: IBinder) {
            val binder = service as SmsForegroundService.LocalBinder
            smsService = binder.getService()
            isBound = true
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
        } else {
            Toast.makeText(this, "SMS Permission is required to send SMS!", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        checkAndRequestPermissions()

        // Load initial persistent logs
        reloadLogs()

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
                    SmsGatewayApp(
                        deviceIp = getDeviceIpAddress(this),
                        isServerRunning = isServerRunningState.value,
                        logs = savedLogsState,
                        onToggleServer = { start ->
                            isServerRunningState.value = start
                            val intent = Intent(this, SmsForegroundService::class.java).apply {
                                action = if (start) SmsForegroundService.ACTION_START_SERVER else SmsForegroundService.ACTION_STOP_SERVER
                            }
                            startService(intent)
                        },
                        onSendSms = { recipient, message ->
                            val words = getWordCount(message)
                            if (words > 500) {
                                Toast.makeText(this, "Error: Message exceeds 500 word limit ($words words)", Toast.LENGTH_LONG).show()
                                return@SmsGatewayApp
                            }
                            
                            val result = SmsSender.sendSms(this, recipient, message)
                            val statusStr = if (result.success) "SUCCESS" else "FAILED: ${result.message}"
                            
                            val logRecord = SmsLogRecord(
                                recipient = recipient,
                                message = message,
                                wordCount = words,
                                status = statusStr
                            )
                            SmsLogStorage.saveLog(this, logRecord)
                            reloadLogs()

                            Toast.makeText(this, result.message, Toast.LENGTH_SHORT).show()
                            smsService?.addLog("Manual SMS -> $recipient [$statusStr]")
                        },
                        onExportLogs = {
                            val msg = SmsLogStorage.exportLogsToCSV(this)
                            Toast.makeText(this, msg, Toast.LENGTH_LONG).show()
                        },
                        onClearLogs = {
                            SmsLogStorage.clearLogs(this)
                            reloadLogs()
                            Toast.makeText(this, "Log history cleared.", Toast.LENGTH_SHORT).show()
                        }
                    )
                }
            }
        }
    }

    private fun reloadLogs() {
        savedLogsState.clear()
        savedLogsState.addAll(SmsLogStorage.getLogs(this))
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isBound) {
            unbindService(connection)
            isBound = false
        }
    }

    private fun checkAndRequestPermissions() {
        val neededPermissions = mutableListOf(Manifest.permission.SEND_SMS)
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

    private fun getDeviceIpAddress(context: Context): String {
        try {
            val interfaces = Collections.list(NetworkInterface.getNetworkInterfaces())
            for (intf in interfaces) {
                val addrs = Collections.list(intf.inetAddresses)
                for (addr in addrs) {
                    if (!addr.isLoopbackAddress) {
                        val host = addr.hostAddress
                        if (host != null && !host.contains(":")) {
                            return host
                        }
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return "127.0.0.1"
    }

    private fun getWordCount(text: String): Int {
        if (text.isBlank()) return 0
        return text.trim().split("\\s+".toRegex()).size
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmsGatewayApp(
    deviceIp: String,
    isServerRunning: Boolean,
    logs: List<SmsLogRecord>,
    onToggleServer: (Boolean) -> Unit,
    onSendSms: (String, String) -> Unit,
    onExportLogs: () -> Unit,
    onClearLogs: () -> Unit
) {
    var recipientPhone by remember { mutableStateOf("") }
    var messageText by remember { mutableStateOf("") }

    val wordCount = remember(messageText) {
        if (messageText.isBlank()) 0 else messageText.trim().split("\\s+".toRegex()).size
    }
    val isWordCountExceeded = wordCount > 500

    var selectedTab by remember { mutableIntStateOf(0) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // App Header
        Text(
            text = "📱 Phone SMS Gateway App",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 6.dp)
        )

        // IP & Status Summary Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(text = "Local Endpoint:", fontSize = 11.sp, color = Color.Gray)
                    Text(
                        text = "http://$deviceIp:8080/send-sms",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        color = Color(0xFF64B5F6)
                    )
                }
                Switch(
                    checked = isServerRunning,
                    onCheckedChange = { onToggleServer(it) }
                )
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Navigation Tabs (Send SMS vs View Logs)
        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("✉️ Send SMS") }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("📋 Logs (${logs.size})") }
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (selectedTab == 0) {
            // TAB 1: SEND SMS FORM
            Column(modifier = Modifier.fillMaxWidth()) {
                Text(text = "Recipient Phone Number", fontWeight = FontWeight.SemiBold)
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = recipientPhone,
                    onValueChange = { recipientPhone = it },
                    placeholder = { Text("+1234567890") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(text = "Message Content", fontWeight = FontWeight.SemiBold)
                    Text(
                        text = "$wordCount / 500 words",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = if (isWordCountExceeded) Color.Red else if (wordCount > 450) Color(0xFFFF9800) else Color(0xFF81C784)
                    )
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
                            onSendSms(recipientPhone, messageText)
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
            // TAB 2: LOGS VIEW & DOWNLOAD
            Column(modifier = Modifier.fillMaxWidth().weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "Sent Messages Log", fontWeight = FontWeight.Bold)
                    Row {
                        Button(
                            onClick = onExportLogs,
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2196F3)),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
                        ) {
                            Text("📥 Download CSV", fontSize = 12.sp)
                        }
                        Spacer(modifier = Modifier.width(6.dp))
                        TextButton(onClick = onClearLogs) {
                            Text("Clear", color = Color.Red, fontSize = 12.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                if (logs.isEmpty()) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color(0xFF1E1E1E), shape = RoundedCornerShape(8.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(text = "No SMS dispatch logs recorded yet.", color = Color.Gray)
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(logs) { log ->
                            SmsLogCard(log)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SmsLogCard(log: SmsLogRecord) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (log.status.startsWith("SUCCESS")) Color(0xFF1B2E1B) else Color(0xFF331B1B)
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
                    color = if (log.status.startsWith("SUCCESS")) Color(0xFF81C784) else Color(0xFFE57373)
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
