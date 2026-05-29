package com.example.greetingcard

import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.gotrue.Auth
import io.github.jan.supabase.postgrest.Postgrest
import io.ktor.client.plugins.HttpTimeout
import io.github.jan.supabase.annotations.SupabaseInternal
import android.util.Log

object SupabaseInstance {
    @OptIn(SupabaseInternal::class)
    val client by lazy {
        Log.d("SupabaseInstance", "Creating SupabaseClient...")
        try {
            val c = createSupabaseClient(
                supabaseUrl = "https://exoctvegujulyephkzep.supabase.co",
                supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4b2N0dmVndWp1bHllcGhremVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1NzcwMjAsImV4cCI6MjA4OTE1MzAyMH0.TE3ldelxi0ag1BLwc-tDSGg-8DSxupnvxMHK77LA2rk"
            ) {
                install(Auth)
                install(Postgrest)
                httpConfig {
                    install(HttpTimeout) {
                        requestTimeoutMillis = 30000
                        connectTimeoutMillis = 30000
                    }
                }
            }
            Log.d("SupabaseInstance", "SupabaseClient created successfully.")
            c
        } catch (e: Exception) {
            Log.e("SupabaseInstance", "Error creating SupabaseClient: ${e.message}")
            throw e
        }
    }
}
