package com.phonesms.server

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.SmsManager
import android.telephony.SubscriptionManager
import androidx.core.content.ContextCompat

object SmsSender {

    fun sendSms(context: Context, destinationAddress: String, message: String): SmsResult {
        // 1. Verify SEND_SMS permission runtime state
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            return SmsResult(
                false,
                "Permission Denied: SEND_SMS permission is missing. Please go to Phone Settings -> Apps -> SMS HTTP Gateway -> Permissions and grant SMS access."
            )
        }

        val cleanPhone = destinationAddress.trim()
        if (cleanPhone.isBlank()) {
            return SmsResult(false, "Invalid recipient: Phone number cannot be empty.")
        }

        return try {
            // 2. Obtain optimal SmsManager for active SIM card
            val smsManager = getBestSmsManager(context)

            // 3. Split multipart message if longer than standard 160 GSM chars
            val parts = smsManager.divideMessage(message)
            if (parts.size > 1) {
                smsManager.sendMultipartTextMessage(cleanPhone, null, parts, null, null)
            } else {
                smsManager.sendTextMessage(cleanPhone, null, message, null, null)
            }

            SmsResult(true, "SMS dispatched successfully to $cleanPhone")
        } catch (e: SecurityException) {
            SmsResult(
                false,
                "Security Exception: SMS permission missing or restricted by OS (${e.localizedMessage})"
            )
        } catch (e: Exception) {
            SmsResult(false, "Failed to send SMS: ${e.localizedMessage ?: e.toString()}")
        }
    }

    private fun getBestSmsManager(context: Context): SmsManager {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val subId = SubscriptionManager.getDefaultSmsSubscriptionId()
            if (subId != SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
                context.getSystemService(SmsManager::class.java).createForSubscriptionId(subId)
            } else {
                context.getSystemService(SmsManager::class.java)
            }
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val subId = SubscriptionManager.getDefaultSmsSubscriptionId()
            if (subId != SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
                @Suppress("DEPRECATION")
                SmsManager.getSmsManagerForSubscriptionId(subId)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }
        } else {
            @Suppress("DEPRECATION")
            SmsManager.getDefault()
        }
    }
}

data class SmsResult(
    val success: Boolean,
    val message: String
)
