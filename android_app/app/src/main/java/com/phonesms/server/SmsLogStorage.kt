package com.phonesms.server

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.io.File
import java.io.OutputStreamWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class SmsLogRecord(
    val id: String = System.currentTimeMillis().toString(),
    val timestamp: String = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date()),
    val recipient: String,
    val message: String,
    val wordCount: Int,
    val status: String // "SUCCESS" or "FAILED: <reason>"
)

object SmsLogStorage {
    private const val TAG = "SmsLogStorage"
    private const val PREF_NAME = "sms_logs_pref"
    private const val KEY_LOGS = "stored_sms_logs"

    fun saveLog(context: Context, logRecord: SmsLogRecord) {
        val current = getLogs(context).toMutableList()
        current.add(0, logRecord) // newest top
        if (current.size > 500) {
            current.removeAt(current.size - 1)
        }
        val json = Gson().toJson(current)
        val pref = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
        pref.edit().putString(KEY_LOGS, json).apply()
    }

    fun getLogs(context: Context): List<SmsLogRecord> {
        val pref = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
        val json = pref.getString(KEY_LOGS, null) ?: return emptyList()
        return try {
            val type = object : TypeToken<List<SmsLogRecord>>() {}.type
            Gson().fromJson(json, type) ?: emptyList()
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing saved logs", e)
            emptyList()
        }
    }

    fun clearLogs(context: Context) {
        val pref = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
        pref.edit().remove(KEY_LOGS).apply()
    }

    /**
     * Export all SMS logs to a downloadable CSV file on the device
     */
    fun exportLogsToCSV(context: Context): String {
        val logs = getLogs(context)
        if (logs.isEmpty()) {
            return "No logs to export."
        }

        val fileName = "SMS_Gateway_Logs_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())}.csv"
        val csvHeader = "ID,Timestamp,Recipient,WordCount,Status,Message\n"
        val csvBody = StringBuilder().append(csvHeader)

        for (item in logs) {
            val safeMessage = item.message.replace("\"", "\"\"").replace("\n", " ")
            csvBody.append("\"${item.id}\",\"${item.timestamp}\",\"${item.recipient}\",${item.wordCount},\"${item.status}\",\"$safeMessage\"\n")
        }

        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val values = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                    put(MediaStore.MediaColumns.MIME_TYPE, "text/csv")
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                }
                val resolver = context.contentResolver
                val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                if (uri != null) {
                    resolver.openOutputStream(uri)?.use { stream ->
                        OutputStreamWriter(stream).use { writer ->
                            writer.write(csvBody.toString())
                        }
                    }
                    "Logs exported to Downloads/$fileName"
                } else {
                    "Failed to create file in Downloads"
                }
            } else {
                @Suppress("DEPRECATION")
                val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                val file = File(downloadsDir, fileName)
                file.writeText(csvBody.toString())
                "Logs exported to Downloads/$fileName"
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error exporting CSV logs", e)
            "Export error: ${e.localizedMessage}"
        }
    }
}
