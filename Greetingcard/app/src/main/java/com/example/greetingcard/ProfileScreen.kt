// ProfileScreen.kt
package com.example.greetingcard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

enum class ProfileCategory { USER_DATA, PREFERENCES }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(onNavigateBack: () -> Unit, authViewModel: AuthViewModel) {
    var selectedCategory by remember { mutableStateOf(ProfileCategory.USER_DATA) }

    // --- WYMUSZENIE ODŚWIEŻENIA PROFILU Z SUPABASE PRZY WEJŚCIU NA EKRAN ---
    LaunchedEffect(Unit) {
        // Wywołujemy checkSession(), które pobiera najnowszy profil z bazy danych
        authViewModel.checkSession()
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Twój Profil", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Wróć")
                    }
                }
            )
        }
    ) { paddingValues ->
        Row(
            modifier = Modifier.fillMaxSize().padding(paddingValues)
        ) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .padding(8.dp)
            ) {
                CategoryItem(
                    text = "Dane użytkownika",
                    isSelected = selectedCategory == ProfileCategory.USER_DATA,
                    onClick = { selectedCategory = ProfileCategory.USER_DATA }
                )
                CategoryItem(
                    text = "Preferencje",
                    isSelected = selectedCategory == ProfileCategory.PREFERENCES,
                    onClick = { selectedCategory = ProfileCategory.PREFERENCES }
                )
            }

            VerticalDivider(modifier = Modifier.fillMaxHeight().width(1.dp))

            Column(
                modifier = Modifier
                    .weight(2f)
                    .fillMaxHeight()
                    .padding(16.dp)
            ) {
                when (selectedCategory) {
                    ProfileCategory.USER_DATA -> UserDataSection(authViewModel)
                    ProfileCategory.PREFERENCES -> PreferencesSection(authViewModel)
                }
            }
        }
    }
}

@Composable
fun CategoryItem(text: String, isSelected: Boolean, onClick: () -> Unit) {
    Text(
        text = text,
        color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 12.dp, horizontal = 8.dp)
    )
}
