package com.phonesms.server

import android.Manifest
import android.app.Activity
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.SmsManager
import android.telephony.SubscriptionInfo
import android.telephony.SubscriptionManager
import android.util.Log
import androidx.core.content.ContextCompat
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

data class SimInfo(
    val subId: Int,
    val slotIndex: Int,
    val carrierName: String,
    val displayName: String
)

object SmsSender {

    private const val ACTION_SMS_SENT = "com.phonesms.server.SMS_SENT"
    private const val TAG = "SmsSender"

    fun getActiveSimCards(context: Context): List<SimInfo> {
        val list = mutableListOf<SimInfo>()
        try {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED) {
                val sm = context.getSystemService(Context.TELEPHONY_SUBSCRIPTION_SERVICE) as? SubscriptionManager
                val activeList: List<SubscriptionInfo>? = sm?.activeSubscriptionInfoList
                activeList?.forEach { info ->
                    val carrier = info.carrierName?.toString()?.takeIf { it.isNotBlank() }
                        ?: info.displayName?.toString()?.takeIf { it.isNotBlank() }
                        ?: "SIM ${info.simSlotIndex + 1}"
                    list.add(
                        SimInfo(
                            subId = info.subscriptionId,
                            slotIndex = info.simSlotIndex + 1,
                            carrierName = carrier,
                            displayName = info.displayName?.toString() ?: "SIM ${info.simSlotIndex + 1}"
                        )
                    )
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error fetching active SIMs", e)
        }
        return list
    }

    fun sendSms(context: Context, destinationAddress: String, message: String, targetSubId: Int? = null): SmsResult {
        // 1. Verify SEND_SMS permission runtime state
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            return SmsResult(
                false,
                "Permission Denied: SEND_SMS permission is missing. Please grant SMS access in Settings."
            )
        }

        val cleanPhone = destinationAddress.trim()
        if (cleanPhone.isBlank()) {
            return SmsResult(false, "Invalid recipient: Phone number cannot be empty.")
        }

        return try {
            val smsManager = getTargetSmsManager(context, targetSubId)

            // 2. Prepare PendingIntent for real-time delivery confirmation
            val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
            val sentIntent = PendingIntent.getBroadcast(
                context,
                0,
                Intent(ACTION_SMS_SENT),
                flags
            )

            var resultStatus = SmsResult(true, "SMS sent to carrier network for $cleanPhone")
            val latch = CountDownLatch(1)

            val sentReceiver = object : BroadcastReceiver() {
                override fun onReceive(c: Context?, intent: Intent?) {
                    val code = resultCode
                    Log.d(TAG, "SMS Sent Broadcast Result Code: $code")
                    resultStatus = when (code) {
                        Activity.RESULT_OK -> SmsResult(true, "SUCCESS: SMS delivered to carrier tower for $cleanPhone")
                        SmsManager.RESULT_ERROR_GENERIC_FAILURE -> SmsResult(
                            false,
                            "FAILED (Generic Error): Carrier or device security blocked the SMS on this SIM."
                        )
                        SmsManager.RESULT_ERROR_NO_SERVICE -> SmsResult(false, "FAILED: No cellular service / SIM not registered.")
                        SmsManager.RESULT_ERROR_NULL_PDU -> SmsResult(false, "FAILED: Null PDU error.")
                        SmsManager.RESULT_ERROR_RADIO_OFF -> SmsResult(false, "FAILED: Radio off / Flight mode enabled.")
                        else -> SmsResult(false, "FAILED: Radio error code $code")
                    }
                    latch.countDown()
                }
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.registerReceiver(sentReceiver, IntentFilter(ACTION_SMS_SENT), Context.RECEIVER_NOT_EXPORTED)
            } else {
                context.registerReceiver(sentReceiver, IntentFilter(ACTION_SMS_SENT))
            }

            try {
                val parts = smsManager.divideMessage(message)
                if (parts.size > 1) {
                    val sentIntents = ArrayList<PendingIntent>()
                    for (i in parts.indices) {
                        sentIntents.add(sentIntent)
                    }
                    smsManager.sendMultipartTextMessage(cleanPhone, null, parts, sentIntents, null)
                } else {
                    smsManager.sendTextMessage(cleanPhone, null, message, sentIntent, null)
                }

                // Wait up to 3 seconds for radio broadcast confirmation
                latch.await(3, TimeUnit.SECONDS)
            } finally {
                try {
                    context.unregisterReceiver(sentReceiver)
                } catch (e: Exception) {
                    // Ignore unregister exception if receiver was already cleared
                }
            }

            resultStatus
        } catch (e: SecurityException) {
            SmsResult(
                false,
                "Security Exception: SMS permission restricted by OS (${e.localizedMessage})"
            )
        } catch (e: Exception) {
            SmsResult(false, "Failed to send SMS: ${e.localizedMessage ?: e.toString()}")
        }
    }

    private fun getTargetSmsManager(context: Context, targetSubId: Int?): SmsManager {
        if (targetSubId != null && targetSubId != SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
            return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                context.getSystemService(SmsManager::class.java).createForSubscriptionId(targetSubId)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getSmsManagerForSubscriptionId(targetSubId)
            }
        }

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
