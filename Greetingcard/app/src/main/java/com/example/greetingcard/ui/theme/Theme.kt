package com.example.greetingcard.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// Tworzymy nasz nowy, "ogórkowy" schemat kolorów
private val AppColorScheme = lightColorScheme(
    primary = PickleGreen,             // Główne przyciski
    onPrimary = TextWhite,             // Tekst na głównych przyciskach
    secondary = DillYellow,            // Przyciski poboczne
    onSecondary = TextDarkGreen,       // Tekst na przyciskach pobocznych
    background = PickleLightBackground,// Jasnozielonkawe tło aplikacji
    onBackground = TextDarkGreen,      // Tekst na głównym tle
    surface = PickleSurface,           // Tła okienek, list rozwijanych itp.
    onSurface = TextDarkGreen          // Tekst na okienkach
)

@Composable
fun GreetingCardTheme(
    content: @Composable () -> Unit
) {
    val colorScheme = AppColorScheme
    val view = LocalView.current
    val context = androidx.compose.ui.platform.LocalContext.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (context as? Activity)?.window
            if (window != null) {
                // Zmieniamy kolor górnego paska na nasze jasne tło
                window.statusBarColor = colorScheme.background.toArgb()
                // Ikony (bateria, zasięg) ciemne, żeby były czytelne
                WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = true
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
