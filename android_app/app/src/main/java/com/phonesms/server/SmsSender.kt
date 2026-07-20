package com.phonesms.server

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.SmsManager
import android.util.Log

object SmsSender {
    private const val TAG = "SmsSender"

    fun sendSms(context: Context, destinationAddress: String, messageText: String): SmsSendResult {
        if (destinationAddress.isBlank() || messageText.isBlank()) {
            return SmsSendResult(false, "Destination phone number or message cannot be empty")
        }

        return try {
            val smsManager: SmsManager = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                context.getSystemService(SmsManager::class.java)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }

            // Split long SMS if necessary
            val parts = smsManager.divideMessage(messageText)
            if (parts.size > 1) {
                smsManager.sendMultipartTextMessage(destinationAddress, null, parts, null, null)
            } else {
                smsManager.sendTextMessage(destinationAddress, null, messageText, null, null)
            }

            Log.i(TAG, "SMS queued to send to $destinationAddress")
            SmsSendResult(true, "SMS dispatched successfully to $destinationAddress")
        } catch (e: Exception) {
            Log.e(TAG, "Error sending SMS to $destinationAddress", e)
            SmsSendResult(false, "Failed to send SMS: ${e.localizedMessage}")
        }
    }
}

data class SmsSendResult(
    val success: Boolean,
    val message: String
)
