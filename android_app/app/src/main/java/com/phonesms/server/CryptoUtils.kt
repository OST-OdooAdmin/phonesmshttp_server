package com.phonesms.server

import android.util.Base64

object CryptoUtils {
    private const val SECRET_KEY = "Dreamer1!_SMS_Key_2026"

    /**
     * Decrypts the Base64 XOR encrypted IP payload fetched from GitHub current_ip.enc
     */
    fun decryptIpPayload(encryptedBase64: String): String {
        return try {
            val cipherBytes = Base64.decode(encryptedBase64.trim(), Base64.DEFAULT)
            val keyBytes = SECRET_KEY.toByteArray(Charsets.UTF_8)
            val plainBytes = ByteArray(cipherBytes.size)
            for (i in cipherBytes.indices) {
                plainBytes[i] = (cipherBytes[i].toInt() xor keyBytes[i % keyBytes.size].toInt()).toByte()
            }
            String(plainBytes, Charsets.UTF_8).trim()
        } catch (e: Exception) {
            ""
        }
    }
}
