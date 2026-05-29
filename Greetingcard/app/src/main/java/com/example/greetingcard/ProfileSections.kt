// ProfileSections.kt
package com.example.greetingcard

import com.example.greetingcard.data.model.IngredientDictionary
import android.widget.Toast
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp

@Composable
fun UserDataSection(authViewModel: AuthViewModel) {
    val currentEmail by authViewModel.currentEmail.collectAsState()
    val currentUsername by authViewModel.currentUsername.collectAsState()
    val context = LocalContext.current

    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Text("Zarządzaj kontem", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(24.dp))

        EditableField(
            label = "Email",
            currentValue = currentEmail ?: "Ładowanie...",
            buttonText = "Zmień mail",
            onSave = { newValue, onResult ->
                authViewModel.updateEmail(newValue) { success, msg ->
                    Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                    onResult(success)
                }
            }
        )

        Divider(modifier = Modifier.padding(vertical = 12.dp))

        EditableField(
            label = "Login",
            currentValue = currentUsername ?: "Ładowanie...",
            buttonText = "Zmień login",
            onSave = { newValue, onResult ->
                authViewModel.updateUsername(newValue) { success, msg ->
                    Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                    onResult(success)
                }
            }
        )

        Divider(modifier = Modifier.padding(vertical = 12.dp))

        EditableField(
            label = "Hasło",
            currentValue = "********",
            buttonText = "Odśwież hasło",
            isPassword = true,
            onSave = { newValue, onResult ->
                authViewModel.updatePassword(newValue) { success, msg ->
                    Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                    onResult(success)
                }
            }
        )

        Spacer(Modifier.height(32.dp))
        TextButton(onClick = { /* W przyszłości: Usuń konto */ }) {
            Text("Usuń konto", color = MaterialTheme.colorScheme.error)
        }
    }
}

@Composable
fun EditableField(
    label: String,
    currentValue: String,
    buttonText: String,
    isPassword: Boolean = false,
    onSave: (String, onResult: (Boolean) -> Unit) -> Unit
) {
    var isEditing by remember { mutableStateOf(false) }
    var tempValue by remember { mutableStateOf("") }
    var tempValueConfirm by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    LaunchedEffect(currentValue) {
        if (!isEditing && !isPassword) {
            tempValue = currentValue
        }
    }

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)

        if (isEditing) {
            OutlinedTextField(
                value = tempValue,
                onValueChange = { tempValue = it },
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                singleLine = true,
                label = { if (isPassword) Text("Nowe hasło") else null },
                visualTransformation = if (isPassword) PasswordVisualTransformation() else VisualTransformation.None
            )

            if (isPassword) {
                OutlinedTextField(
                    value = tempValueConfirm,
                    onValueChange = { tempValueConfirm = it },
                    modifier = Modifier.fillMaxWidth().padding(bottom = 4.dp),
                    singleLine = true,
                    label = { Text("Powtórz nowe hasło") },
                    visualTransformation = PasswordVisualTransformation()
                )
            }

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                TextButton(
                    onClick = {
                        isEditing = false
                        tempValue = if (isPassword) "" else currentValue
                        tempValueConfirm = ""
                    },
                    enabled = !isLoading
                ) {
                    Text("Anuluj", color = MaterialTheme.colorScheme.error)
                }
                Spacer(Modifier.width(8.dp))
                Button(
                    onClick = {
                        isLoading = true
                        onSave(tempValue) { success ->
                            isLoading = false
                            if (success) {
                                isEditing = false
                                if (isPassword) {
                                    tempValue = ""
                                    tempValueConfirm = ""
                                }
                            }
                        }
                    },
                    enabled = !isLoading && tempValue.isNotBlank() && tempValue != currentValue && (!isPassword || tempValue == tempValueConfirm)
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                    } else {
                        Text("Zapisz")
                    }
                }
            }
        } else {
            Row(
                modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = currentValue,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.weight(1f)
                )
                OutlinedButton(
                    onClick = {
                        isEditing = true
                        if (isPassword) {
                            tempValue = ""
                            tempValueConfirm = ""
                        }
                    }
                ) {
                    Text(buttonText)
                }
            }
        }
    }
}

@Composable
fun PreferencesSection(authViewModel: AuthViewModel) {
    // 1. Podpinamy się pod aktualny profil użytkownika
    val userProfile by authViewModel.userProfile.collectAsState()
    val context = LocalContext.current

    // 2. Inicjalizujemy stany list wartościami pobranymi z bazy danych
    var excludedIngredients by remember(userProfile) { mutableStateOf(userProfile?.excluded_ingredients ?: emptyList()) }
    var dislikedIngredients by remember(userProfile) { mutableStateOf(userProfile?.disliked_ingredients ?: emptyList()) }
    var likedIngredients by remember(userProfile) { mutableStateOf(userProfile?.liked_ingredients ?: emptyList()) }
    var selectedDiets by remember(userProfile) { mutableStateOf((userProfile?.diets ?: emptyList()).toSet()) }
    var showDietDialog by remember { mutableStateOf(false) }

    val allAvailableIngredients = remember { IngredientDictionary.getDisplayNames() }

    // 3. Funkcja pomocnicza: Wywołuje zapis do bazy z aktualnymi wartościami
    fun savePreferences(
        excluded: List<String> = excludedIngredients,
        disliked: List<String> = dislikedIngredients,
        liked: List<String> = likedIngredients,
        diets: List<String> = selectedDiets.toList()
    ) {
        authViewModel.updatePreferences(
            excluded = excluded,
            disliked = disliked,
            liked = liked,
            diets = diets
        ) { _, msg ->
            // Opcjonalnie: Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(bottom = 16.dp)
    ) {
        Text("Twoje preferencje", style = MaterialTheme.typography.titleLarge)
        
        Spacer(Modifier.height(16.dp))

        Text(
            "Wybrane diety: ${if (selectedDiets.isEmpty()) "Brak" else selectedDiets.joinToString()}",
            style = MaterialTheme.typography.bodyMedium
        )
        Button(onClick = { showDietDialog = true }, modifier = Modifier.padding(top = 8.dp)) {
            Text("Wybierz diety")
        }

        Spacer(Modifier.height(24.dp))

        IngredientListEditor(
            title = "Wykluczone składniki",
            items = excludedIngredients,
            availableIngredients = allAvailableIngredients,
            onItemsChanged = { newItems ->
                excludedIngredients = newItems
                savePreferences(excluded = newItems)
            }
        )

        Spacer(Modifier.height(16.dp))

        IngredientListEditor(
            title = "Nielubiane składniki",
            items = dislikedIngredients,
            availableIngredients = allAvailableIngredients,
            onItemsChanged = { newItems ->
                dislikedIngredients = newItems
                savePreferences(disliked = newItems)
            }
        )

        Spacer(Modifier.height(16.dp))

        IngredientListEditor(
            title = "Lubiane składniki",
            items = likedIngredients,
            availableIngredients = allAvailableIngredients,
            onItemsChanged = { newItems ->
                likedIngredients = newItems
                savePreferences(liked = newItems)
            }
        )

        if (showDietDialog) {
            DietSelectionDialog(
                currentSelections = selectedDiets,
                onDismiss = { showDietDialog = false },
                onConfirm = { newSelections ->
                    selectedDiets = newSelections
                    savePreferences(diets = newSelections.toList())
                    showDietDialog = false
                }
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
fun IngredientListEditor(
    title: String,
    items: List<String>,
    availableIngredients: List<String>,
    onItemsChanged: (List<String>) -> Unit
) {
    var showSelectionDialog by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(title, style = MaterialTheme.typography.titleMedium)

        Button(onClick = { showSelectionDialog = true }, modifier = Modifier.padding(top = 8.dp)) {
            Text("Dodaj składniki")
        }

        FlowRow(
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items.forEach { item ->
                InputChip(
                    selected = false,
                    onClick = { },
                    label = { Text(item) },
                    trailingIcon = {
                        Icon(
                            Icons.Default.Close,
                            contentDescription = "Usuń",
                            modifier = Modifier.clickable {
                                onItemsChanged(items.filter { it != item })
                            }
                        )
                    }
                )
            }
        }

        if (showSelectionDialog) {
            SearchableSelectionDialog(
                title = "Wybierz składniki",
                availableItems = availableIngredients,
                currentSelections = items.toSet(),
                onDismiss = { showSelectionDialog = false },
                onConfirm = { newSelections ->
                    onItemsChanged(newSelections.toList())
                    showSelectionDialog = false
                }
            )
        }
    }
}

@Composable
fun SearchableSelectionDialog(
    title: String,
    availableItems: List<String>,
    currentSelections: Set<String>,
    onDismiss: () -> Unit,
    onConfirm: (Set<String>) -> Unit
) {
    var searchQuery by remember { mutableStateOf("") }
    var tempSelections by remember { mutableStateOf(currentSelections) }

    val filteredItems = availableItems.filter {
        it.contains(searchQuery, ignoreCase = true)
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    label = { Text("Szukaj...") },
                    modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                    singleLine = true,
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(Icons.Default.Close, contentDescription = "Wyczyść")
                            }
                        }
                    }
                )

                // KLUCZOWA ZMIANA: Zamiast weight(1f), dajemy heightIn(max = 350.dp).
                // To zmusza listę do włączenia scrollowania, jeśli elementów jest dużo!
                Box(modifier = Modifier.heightIn(max = 350.dp)) {
                    if (filteredItems.isEmpty()) {
                        Text(
                            "Brak wyników.",
                            modifier = Modifier.padding(vertical = 16.dp),
                            style = MaterialTheme.typography.bodyMedium
                        )
                    } else {
                        // LazyColumn odpowiada za scrollowanie na Androidzie
                        LazyColumn(modifier = Modifier.fillMaxWidth()) {
                            items(filteredItems) { item ->
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable {
                                            tempSelections = if (tempSelections.contains(item)) {
                                                tempSelections - item
                                            } else {
                                                tempSelections + item
                                            }
                                        }
                                        .padding(vertical = 4.dp)
                                ) {
                                    Checkbox(
                                        checked = tempSelections.contains(item),
                                        onCheckedChange = null
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(text = item)
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(onClick = { onConfirm(tempSelections) }) {
                Text("Zatwierdź")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Anuluj")
            }
        }
    )
}
@Composable
fun DietSelectionDialog(
    currentSelections: Set<String>,
    onDismiss: () -> Unit,
    onConfirm: (Set<String>) -> Unit
) {
    val availableDiets = remember {
        listOf(
            "Bez nabiału", "Bezglutenowa", "Keto", "Low FODMAP",
            "Paleo", "Primal", "Wegańska", "Wegetariańska", "Whole30"
        ).sorted()
    }

    SearchableSelectionDialog(
        title = "Wybierz diety",
        availableItems = availableDiets,
        currentSelections = currentSelections,
        onDismiss = onDismiss,
        onConfirm = onConfirm
    )
}
