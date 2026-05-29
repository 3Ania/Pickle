package com.example.greetingcard

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SurveyScreen(
    authViewModel: AuthViewModel,
    recommendationViewModel: RecommendationViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToResults: () -> Unit
) {
    val userProfile by authViewModel.userProfile.collectAsState()

    // NOWE STANY: Pole tekstowe na opis oraz flaga braku limitu czasu
    var userPrompt by remember { mutableStateOf("") }
    var noTimeLimit by remember { mutableStateOf(false) }

    var maxTime by remember { mutableStateOf(30f) }
    var tempPreference by remember { mutableStateOf<Boolean?>(null) }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Dostrój rekomendację", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Wróć")
                    }
                }
            )
        },
        bottomBar = {
            Surface(tonalElevation = 8.dp) {
                Button(
                    onClick = {
                        if (userProfile != null) {
                            recommendationViewModel.getQuickRecommendations(
                                profile = userProfile,
                                userPrompt = userPrompt,
                                maxTime = if (noTimeLimit) null else maxTime.toInt(),
                                isWarm = tempPreference
                            )
                            onNavigateToResults()
                        }
                    },
                    modifier = Modifier.fillMaxWidth().padding(16.dp).height(56.dp)
                ) {
                    val timeText = if (noTimeLimit) "Dowolny czas" else "${maxTime.toInt()} min"
                    Text("Znajdź przepisy ($timeText)", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Sekcja: INTELIGENTNY OPIS
            Text("Na co masz dzisiaj ochotę?", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Napisz własnymi słowami co chcesz zjeść, jakich składników użyć, a czego unikać (np. 'Ziemniaki na ciepło z czosnkiem, ale bez papryki i grzybów').",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = userPrompt,
                onValueChange = { userPrompt = it },
                modifier = Modifier.fillMaxWidth().height(140.dp),
                placeholder = { Text("Wpisz swoje zachcianki kulinarne...") },
                maxLines = 5
            )

            Spacer(modifier = Modifier.height(28.dp))

            // Sekcja: CZAS PRZYGOTOWANIA
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Maksymalny czas przygotowania", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)

                // Checkbox wyłączający limit czasu
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = noTimeLimit, onCheckedChange = { noTimeLimit = it })
                    Text("Brak limitu", style = MaterialTheme.typography.bodyMedium)
                }
            }

            if (noTimeLimit) {
                Text("Dowolny (uwzględnia długie przepisy)", color = MaterialTheme.colorScheme.secondary, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(16.dp))
            } else {
                Text("${maxTime.toInt()} minut", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                Slider(
                    value = maxTime,
                    onValueChange = { maxTime = it },
                    valueRange = 10f..120f,
                    steps = 10
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Sekcja: TEMPERATURA
            Text("Temperatura posiłku", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                FilterChip(selected = tempPreference == true, onClick = { tempPreference = true }, label = { Text("Ciepłe") })
                FilterChip(selected = tempPreference == false, onClick = { tempPreference = false }, label = { Text("Zimne") })
                FilterChip(selected = tempPreference == null, onClick = { tempPreference = null }, label = { Text("Obojętnie") })
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}
