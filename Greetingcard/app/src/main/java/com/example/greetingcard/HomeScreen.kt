// HomeScreen.kt
package com.example.greetingcard

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

@Composable
fun HomeScreen(
    username: String,
    onNavigateToProfile: () -> Unit,
    onNavigateToQuickRecommendation: () -> Unit,
    onNavigateToSurvey: () -> Unit,
    onLogout: () -> Unit
) {
    val context = LocalContext.current
    var expanded by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize()) {
        // Górny pasek z Avatarem i Menu
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            horizontalArrangement = Arrangement.End,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box {
                // Avatar, który po kliknięciu rozwija menu
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(MaterialTheme.colorScheme.primary, CircleShape)
                        .clickable { expanded = true },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = username.take(1).uppercase(),
                        color = Color.White,
                        style = MaterialTheme.typography.titleLarge
                    )
                }

                // Menu rozwijane (Dropdown)
                DropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    DropdownMenuItem(
                        text = { Text("Twój Profil") },
                        onClick = {
                            expanded = false
                            onNavigateToProfile()
                        }
                    )
                    Divider()
                    DropdownMenuItem(
                        text = { Text("Wyloguj", color = MaterialTheme.colorScheme.error) },
                        onClick = {
                            expanded = false
                            onLogout()
                        }
                    )
                }
            }
        }

        // Środek ekranu z przyciskami akcji
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Witaj, $username!",
                style = MaterialTheme.typography.headlineMedium
            )

            Spacer(Modifier.height(32.dp))

            // Przycisk rekomendacji - teraz poprawnie podpięty
            Button(
                onClick = onNavigateToQuickRecommendation,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
            ) {
                Text("Szybka rekomendacja")
            }

            Spacer(Modifier.height(16.dp))

            // Przycisk ankiety (na razie Toast)
            Button(
                onClick = onNavigateToSurvey,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary
                )
            ) {
                Text("Wypełnij ankietę dla dokładniejszej rekomendacji")
            }
        }
    }
}
