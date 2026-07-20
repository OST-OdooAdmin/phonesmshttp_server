package com.phonesms.server

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class SmsForegroundService : Service() {

    private val binder = LocalBinder()
    private var httpServerEngine: HttpServerEngine? = null
    private var pollingEngine: PollingEngine? = null

    val logs = mutableListOf<String>()
    var onLogListener: ((String) -> Unit)? = null

    inner class LocalBinder : Binder() {
        fun getService(): SmsForegroundService = this@SmsForegroundService
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification("SMS Gateway Active"))
        
        httpServerEngine = HttpServerEngine(this, 8080) { log ->
            addLog(log)
        }
        pollingEngine = PollingEngine(this) { log ->
            addLog(log)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        when (action) {
            ACTION_START_SERVER -> {
                val port = intent.getIntExtra(EXTRA_PORT, 8080)
                httpServerEngine?.start()
            }
            ACTION_STOP_SERVER -> {
                httpServerEngine?.stop()
            }
            ACTION_START_POLLING -> {
                val url = intent.getStringExtra(EXTRA_URL) ?: ""
                val apiKey = intent.getStringExtra(EXTRA_API_KEY) ?: ""
                pollingEngine?.startPolling(url, apiKey)
            }
            ACTION_STOP_POLLING -> {
                pollingEngine?.stopPolling()
            }
        }
        return START_STICKY
    }

    fun addLog(message: String) {
        val formatted = "[${System.currentTimeMillis() % 100000 / 1000}s] $message"
        logs.add(0, formatted) // newest on top
        if (logs.size > 200) logs.removeAt(logs.size - 1)
        onLogListener?.invoke(formatted)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "SMS HTTP Gateway Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(contentText: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("SMS HTTP Gateway")
            .setContentText(contentText)
            .setSmallIcon(android.R.drawable.stat_notify_chat)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "SmsGatewayChannel"
        private const val NOTIFICATION_ID = 1001

        const val ACTION_START_SERVER = "com.phonesms.server.START_SERVER"
        const val ACTION_STOP_SERVER = "com.phonesms.server.STOP_SERVER"
        const val ACTION_START_POLLING = "com.phonesms.server.START_POLLING"
        const val ACTION_STOP_POLLING = "com.phonesms.server.STOP_POLLING"

        const val EXTRA_PORT = "extra_port"
        const val EXTRA_URL = "extra_url"
        const val EXTRA_API_KEY = "extra_api_key"
    }
}
