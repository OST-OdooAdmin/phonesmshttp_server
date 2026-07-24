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
    val id: Int,
    val to: String,
    val message: String
)

data class PendingSmsResponse(
    val pending: List<SmsTask>
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

    fun startPolling(serverUrl: String, apiKey: String, intervalSeconds: Int = 5) {
        if (pollingJob != null && pollingJob?.isActive == true) return
        if (serverUrl.isBlank()) {
            onLog("Polling skipped: No server URL provided.")
            return
        }

        pollingJob = CoroutineScope(Dispatchers.IO).launch {
            onLog("Started Odoo Polling Client -> $serverUrl (Interval: ${intervalSeconds}s)")

            val pendingUrl = if (serverUrl.endsWith("/")) "${serverUrl}api/sms/pending" else "$serverUrl/api/sms/pending"
            val statusUrl = if (serverUrl.endsWith("/")) "${serverUrl}api/sms/status" else "$serverUrl/api/sms/status"

            while (isActive) {
                try {
                    val response: PendingSmsResponse = httpClient.get(pendingUrl) {
                        header("X-Api-Key", apiKey)
                    }.body()

                    if (response.pending.isNotEmpty()) {
                        onLog("Retrieved ${response.pending.size} pending SMS tasks from Odoo")
                        for (task in response.pending) {
                            onLog("Processing task #${task.id} -> ${task.to}")
                            
                            val words = if (task.message.isBlank()) 0 else task.message.trim().split("\\s+".toRegex()).size
                            val result = SmsSender.sendSms(context, task.to, task.message)
                            val statusStr = if (result.success) "SUCCESS" else "FAILED: ${result.message}"
                            
                            // Save to local persistent logs silently
                            val logRecord = SmsLogRecord(
                                recipient = task.to,
                                message = task.message,
                                wordCount = words,
                                status = statusStr
                            )
                            SmsLogStorage.saveLog(context, logRecord)
                            
                            // Post receipt back to Odoo
                            try {
                                httpClient.post(statusUrl) {
                                    header("X-Api-Key", apiKey)
                                    contentType(ContentType.Application.Json)
                                    setBody(
                                        SmsStatusReport(
                                            task_id = task.id,
                                            status = if (result.success) "sent" else "failed",
                                            detail = result.message
                                        )
                                    )
                                }
                                onLog("Reported status for task #${task.id} to Odoo")
                            } catch (e: Exception) {
                                Log.e(TAG, "Failed to report status for task #${task.id}", e)
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Polling error", e)
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
