package com.phonesms.server

import android.content.Context
import android.util.Log
import io.ktor.http.HttpStatusCode
import io.ktor.serialization.gson.gson
import io.ktor.server.application.call
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.netty.NettyApplicationEngine
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class HttpServerEngine(
    private val context: Context,
    private val port: Int = 8080,
    private val onLog: (String) -> Unit
) {
    private var serverEngine: NettyApplicationEngine? = null
    private const val TAG = "HttpServerEngine"

    fun start() {
        if (serverEngine != null) return

        CoroutineScope(Dispatchers.IO).launch {
            try {
                onLog("Starting HTTP Server on port $port...")
                serverEngine = embeddedServer(Netty, port = port) {
                    install(ContentNegotiation) {
                        gson()
                    }
                    routing {
                        get("/status") {
                            call.respond(
                                mapOf(
                                    "status" to "online",
                                    "device" to "Android SMS Gateway",
                                    "timestamp" to System.currentTimeMillis()
                                )
                            )
                        }

                        post("/send-sms") {
                            try {
                                val request = call.receive<SmsApiRequest>()
                                onLog("Received HTTP SMS request for: ${request.to}")
                                
                                val result = SmsSender.sendSms(context, request.to, request.message)
                                if (result.success) {
                                    onLog("SUCCESS: Sent SMS to ${request.to}")
                                    call.respond(
                                        HttpStatusCode.OK,
                                        SmsApiResponse(
                                            status = "success",
                                            detail = result.message,
                                            timestamp = System.currentTimeMillis()
                                        )
                                    )
                                } else {
                                    onLog("FAILED: ${result.message}")
                                    call.respond(
                                        HttpStatusCode.InternalServerError,
                                        SmsApiResponse(
                                            status = "error",
                                            detail = result.message,
                                            timestamp = System.currentTimeMillis()
                                        )
                                    )
                                }
                            } catch (e: Exception) {
                                Log.e(TAG, "Error handling POST /send-sms", e)
                                onLog("ERROR parsing payload: ${e.localizedMessage}")
                                call.respond(
                                    HttpStatusCode.BadRequest,
                                    SmsApiResponse(
                                        status = "error",
                                        detail = "Invalid JSON payload: ${e.localizedMessage}",
                                        timestamp = System.currentTimeMillis()
                                    )
                                )
                            }
                        }
                    }
                }.start(wait = false)

                onLog("HTTP Server successfully listening on port $port")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to start HTTP server", e)
                onLog("CRITICAL: Failed to start HTTP server: ${e.localizedMessage}")
            }
        }
    }

    fun stop() {
        serverEngine?.stop(1000, 2000)
        serverEngine = null
        onLog("HTTP Server stopped.")
    }
}

data class SmsApiRequest(
    val to: String,
    val message: String
)

data class SmsApiResponse(
    val status: String,
    val detail: String,
    val timestamp: Long
)
