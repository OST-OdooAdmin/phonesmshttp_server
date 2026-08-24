package com.phonesms.server

import android.content.Context
import android.util.Log
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.gson.gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class SmsTask(
    val id: Int = 0,
    val to: String = "",
    val message: String = ""
)

data class PendingSmsResponse(
    val pending: List<SmsTask> = emptyList()
)

data class ServerLogsResponse(
    val logs: List<SmsLogRecord> = emptyList()
)

data class SmsStatusReport(
    val task_id: Int,
    val status: String,
    val detail: String
)

class PollingEngine(
    private val context: Context,
    private val onIpChanged: ((newServerUrl: String) -> Unit)? = null,
    private val onLog: (String) -> Unit
) {
    private var pollingJob: Job? = null
    private val TAG = "PollingEngine"
    private var consecutiveErrorCount = 0
    private var activeServerUrl = ""

    private val httpClient by lazy {
        HttpClient(CIO) {
            install(ContentNegotiation) {
                gson()
            }
            install(HttpTimeout) {
                requestTimeoutMillis = 8000
                connectTimeoutMillis = 6000
                socketTimeoutMillis = 8000
            }
        }
    }

    suspend fun fetchServerLogs(serverUrl: String, apiKey: String): List<SmsLogRecord> {
        if (serverUrl.isBlank()) return emptyList()
        val logsUrl = if (serverUrl.endsWith("/")) "${serverUrl}api/sms/logs" else "$serverUrl/api/sms/logs"
        return try {
            val response: ServerLogsResponse = httpClient.get(logsUrl) {
                header("X-Api-Key", apiKey)
            }.body()
            response.logs ?: emptyList()
        } catch (t: Throwable) {
            Log.e(TAG, "Failed to fetch server logs safely: ${t.message}")
            emptyList()
        }
    }

    fun startPolling(
        serverUrl: String,
        apiKey: String,
        intervalSeconds: Int = 60,
        pacingDelayMs: Long = 1500L
    ) {
        stopPolling() // Ensure previous polling job is cancelled when URL/settings change
        
        if (serverUrl.isBlank()) {
            onLog("Polling skipped: No server URL provided.")
            return
        }

        activeServerUrl = serverUrl.trim()
        consecutiveErrorCount = 0

        pollingJob = CoroutineScope(Dispatchers.IO).launch {
            onLog("Started Local Server Polling Client -> $activeServerUrl (Interval: ${intervalSeconds}s, Bulk Pacing: ${pacingDelayMs / 1000.0}s)")

            while (isActive) {
                val pendingUrl = if (activeServerUrl.endsWith("/")) "${activeServerUrl}pending" else "$activeServerUrl/pending"
                val statusUrl = if (activeServerUrl.endsWith("/")) "${activeServerUrl}status" else "$activeServerUrl/status"

                try {
                    val response: PendingSmsResponse = httpClient.get(pendingUrl) {
                        header("X-Api-Key", apiKey)
                    }.body()

                    consecutiveErrorCount = 0 // Connection successful, reset error counter
                    val pendingList = response.pending
                    if (pendingList != null && pendingList.isNotEmpty()) {
                        onLog("Retrieved ${pendingList.size} pending SMS tasks from server batch")
                        
                        for ((index, task) in pendingList.withIndex()) {
                            if (!isActive) break
                            
                            if (task.to.isNotBlank()) {
                                onLog("Processing task #${task.id} (${index + 1}/${pendingList.size}) -> ${task.to}")
                                
                                val result = SmsSender.sendSms(context, task.to, task.message)
                                val statusStr = if (result.success) "sent" else "failed"
                                
                                try {
                                    httpClient.post(statusUrl) {
                                        header("X-Api-Key", apiKey)
                                        contentType(ContentType.Application.Json)
                                        setBody(
                                            SmsStatusReport(
                                                task_id = task.id,
                                                status = statusStr,
                                                detail = result.message
                                            )
                                        )
                                    }
                                    onLog("Reported status for task #${task.id} [${statusStr.uppercase()}]")
                                } catch (e: Exception) {
                                    Log.e(TAG, "Failed to report status for task #${task.id}", e)
                                }

                                // Bulk Pacing Delay to prevent telco anti-spam carrier locks
                                if (index < pendingList.size - 1 && pacingDelayMs > 0) {
                                    onLog("Pacing delay: Waiting ${pacingDelayMs / 1000.0}s before next SMS...")
                                    delay(pacingDelayMs)
                                }
                            }
                        }
                    }
                } catch (t: Throwable) {
                    consecutiveErrorCount++
                    onLog("⚠️ Server Connection Error (${consecutiveErrorCount}x): ${t.message}")
                    Log.e(TAG, "Polling error handled safely: ${t.message}")

                    // After 2 consecutive connection failures, perform GitHub IP resolution fallback
                    if (consecutiveErrorCount >= 2) {
                        onLog("🔍 Server connection unreachable. Checking GitHub for updated Server IP...")
                        checkAndSwitchIpFromGithub(activeServerUrl)
                    }
                }

                delay(intervalSeconds * 1000L)
            }
        }
    }

    private suspend fun checkAndSwitchIpFromGithub(currentUrl: String) {
        val githubRawEndpoints = listOf(
            "https://raw.githubusercontent.com/MLAU-code/phonesmshttp_server/main/current_ip.enc",
            "https://raw.githubusercontent.com/YOUR_USERNAME/phonesmshttp_server/main/current_ip.enc"
        )

        for (endpoint in githubRawEndpoints) {
            try {
                val responseText: String = httpClient.get(endpoint).body()
                if (responseText.isNotBlank()) {
                    val decryptedIp = CryptoUtils.decryptIpPayload(responseText)
                    if (decryptedIp.isNotBlank() && isValidIpAddress(decryptedIp)) {
                        val newServerUrl = "http://$decryptedIp:22"
                        if (newServerUrl != currentUrl) {
                            onLog("🌐 GITHUB DYNAMIC IP DETECTED: New IP is $decryptedIp (Server URL: $newServerUrl)")
                            val timeStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())

                            // 1. Dispatch SMS Alert to user phone number +65 96780253
                            val alertMsg = "[ALERT] Phone App detected Kuching Server IP changed to $decryptedIp at $timeStr"
                            val smsResult = SmsSender.sendSms(context, "+6596780253", alertMsg)
                            onLog("📱 Sent IP Alert SMS to +6596780253 -> ${if (smsResult.success) "SUCCESS" else "FAILED: ${smsResult.message}"}")

                            // 2. Switch Active Server URL & Notify App
                            activeServerUrl = newServerUrl
                            consecutiveErrorCount = 0
                            onIpChanged?.invoke(newServerUrl)
                            return
                        } else {
                            onLog("GitHub IP matches current target ($decryptedIp). Waiting for server connection to restore...")
                            return
                        }
                    }
                }
            } catch (e: Exception) {
                Log.d(TAG, "GitHub IP lookup on $endpoint skipped: ${e.message}")
            }
        }
    }

    private fun isValidIpAddress(ip: String): Boolean {
        val parts = ip.trim().split(".")
        if (parts.size != 4) return false
        return parts.all { part ->
            part.toIntOrNull()?.let { it in 0..255 } ?: false
        }
    }

    fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
        onLog("Polling engine stopped.")
    }
}
