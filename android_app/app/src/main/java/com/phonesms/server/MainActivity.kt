package com.phonesms.server

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.text.format.Formatter
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
import androidx.compose.ui.platform.LocalContext
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

    private val logsList = mutableStateListOf<String>()
    private var isServerRunningState = mutableStateOf(false)

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(className: ComponentName, service: IBinder) {
            val binder = service as SmsForegroundService.LocalBinder
            smsService = binder.getService()
            isBound = true

            // Attach logs
            smsService?.logs?.let { existing ->
                logsList.clear()
                logsList.addAll(existing)
            }
            smsService?.onLogListener = { newLog ->
                logsList.add(0, newLog)
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
        } else {
            Toast.makeText(this, "SMS Permission is required to send SMS!", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate()
        checkAndRequestPermissions()

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
                    GatewayMainScreen(
                        deviceIp = getDeviceIpAddress(this),
                        isServerRunning = isServerRunningState.value,
                        logs = logsList,
                        onToggleServer = { start ->
                            isServerRunningState.value = start
                            val intent = Intent(this, SmsForegroundService::class.java).apply {
                                action = if (start) SmsForegroundService.ACTION_START_SERVER else SmsForegroundService.ACTION_STOP_SERVER
                            }
                            startService(intent)
                        },
                        onSendManualSms = { phone, msg ->
                            val result = SmsSender.sendSms(this, phone, msg)
                            Toast.makeText(this, result.message, Toast.LENGTH_SHORT).show()
                            smsService?.addLog("Manual Test SMS -> $phone (${if (result.success) "SUCCESS" else "FAILED"})")
                        }
                    )
                }
            }
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
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GatewayMainScreen(
    deviceIp: String,
    isServerRunning: Boolean,
    logs: List<String>,
    onToggleServer: (Boolean) -> Unit,
    onSendManualSms: (String, String) -> Unit
) {
    var testPhone by remember { mutableStateOf("") }
    var testMessage by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Header Banner
        Text(
            text = "📱 Phone SMS HTTP Gateway",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        // IP Connection Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 4.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "Local Wi-Fi Endpoint:", fontSize = 12.sp, color = Color.Gray)
                Text(
                    text = "http://$deviceIp:8080/send-sms",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    color = Color(0xFF64B5F6)
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Server Toggle Switch
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = "HTTP Server Engine", fontWeight = FontWeight.SemiBold)
                Text(
                    text = if (isServerRunning) "Status: RUNNING (:8080)" else "Status: STOPPED",
                    fontSize = 12.sp,
                    color = if (isServerRunning) Color(0xFF81C784) else Color(0xFFE57373)
                )
            }
            Switch(
                checked = isServerRunning,
                onCheckedChange = { onToggleServer(it) }
            )
        }

        Divider(modifier = Modifier.padding(vertical = 12.dp))

        // Manual Test Dispatch Section
        Text(text = "Manual SMS Test Dispatch", fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(6.dp))
        OutlinedTextField(
            value = testPhone,
            onValueChange = { testPhone = it },
            label = { Text("Recipient Phone (+1234567890)") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(modifier = Modifier.height(6.dp))
        OutlinedTextField(
            value = testMessage,
            onValueChange = { testMessage = it },
            label = { Text("Test Message Text") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = {
                if (testPhone.isNotBlank() && testMessage.isNotBlank()) {
                    onSendManualSms(testPhone, testMessage)
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Send Test SMS")
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Live Log Terminal
        Text(text = "Live Dispatch Logs", fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(4.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .background(Color(0xFF000000), shape = RoundedCornerShape(8.dp))
                .padding(8.dp)
        ) {
            if (logs.isEmpty()) {
                Text(
                    text = "No log activity yet. Toggle HTTP server ON or send a test SMS...",
                    color = Color.DarkGray,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
            } else {
                LazyColumn {
                    items(logs) { logLine ->
                        Text(
                            text = logLine,
                            color = Color(0xFF00FF66),
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
