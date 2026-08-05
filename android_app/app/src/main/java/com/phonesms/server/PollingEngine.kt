package com.phonesms.server

import android.content.Context
import android.util.Log
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.cio.CIO
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
    private val onLog: (String) -> Unit
) {
    private var pollingJob: Job? = null
    private val TAG = "PollingEngine"

    private val httpClient by lazy {
        HttpClient(CIO) {
            install(ContentNegotiation) {
                gson()
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

        pollingJob = CoroutineScope(Dispatchers.IO).launch {
            onLog("Started Local Server Polling Client -> $serverUrl (Interval: ${intervalSeconds}s, Bulk Pacing: ${pacingDelayMs / 1000.0}s)")

            val pendingUrl = if (serverUrl.endsWith("/")) "${serverUrl}pending" else "$serverUrl/pending"
            val statusUrl = if (serverUrl.endsWith("/")) "${serverUrl}status" else "$serverUrl/status"

            while (isActive) {
                try {
                    val response: PendingSmsResponse = httpClient.get(pendingUrl) {
                        header("X-Api-Key", apiKey)
                    }.body()

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
                    Log.e(TAG, "Polling error handled safely: ${t.message}")
                }

                delay(intervalSeconds * 1000L)
            }
        }
    }

    fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
        onLog("Polling engine stopped.")
    }
}
