package com.example.greetingcard

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.greetingcard.data.repository.RecommendationEngine
import com.example.greetingcard.ui.theme.GreetingCardTheme
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.font.FontWeight

import android.util.Log

// Nawigator po ekranach
enum class Screen {
    LOGIN, REGISTER, HOME, PROFILE, QUICK_RECOMMENDATION, SURVEY
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("MainActivity", "onCreate started")
        setContent {
            GreetingCardTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainApp()
                }
            }
        }
    }
}

@Composable
fun MainApp(authViewModel: AuthViewModel = viewModel()) {
    // Nasłuchiwanie stanów z AuthViewModel
    val currentUsername by authViewModel.currentUsername.collectAsState()
    val userProfile by authViewModel.userProfile.collectAsState()
    var currentScreen by remember { mutableStateOf(Screen.LOGIN) }

    // Stan inicjalizacji silnika rekomendacji
    var engine by remember { mutableStateOf<RecommendationEngine?>(null) }
    var engineInitializationError by remember { mutableStateOf<String?>(null) }

    // Inicjalizacja silnika w tle - zapobiega blokowaniu Main Thread (ANR)
    LaunchedEffect(Unit) {
        try {
            Log.d("MainApp", "Rozpoczynam inicjalizację silnika w tle...")
            val initializedEngine = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                // SupabaseInstance.client jest lazy, więc to wywołanie uruchomi jego tworzenie na wątku IO
                RecommendationEngine(SupabaseInstance.client)
            }
            engine = initializedEngine
            Log.d("MainApp", "Silnik zainicjalizowany pomyślnie.")
        } catch (e: Exception) {
            Log.e("MainApp", "BŁĄD inicjalizacji silnika: ${e.message}")
            engineInitializationError = e.message ?: "Nieznany błąd"
        }
    }

    // AUTO-LOGIN: Jeśli użytkownik jest już zalogowany, przejdź do HOME
    LaunchedEffect(currentUsername) {
        if (currentUsername != null && currentScreen == Screen.LOGIN) {
            Log.d("MainApp", "Auto-login detected for: $currentUsername. Switching to HOME.")
            currentScreen = Screen.HOME
        }
    }

    // Ekran błędu krytycznego
    if (engineInitializationError != null) {
        Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            Text(
                "Wystąpił błąd podczas uruchamiania aplikacji:\n$engineInitializationError",
                color = Color.Red,
                style = MaterialTheme.typography.bodyLarge
            )
        }
        return
    }

    // Ekran ładowania (SplashScreen)
    if (engine == null) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator()
                Spacer(Modifier.height(16.dp))
                Text("Ładowanie zasobów...", style = MaterialTheme.typography.bodyMedium)
            }
        }
        return
    }
    
    // Inicjalizacja ViewModelu rekomendacji po upewnieniu się, że engine jest gotowy
    val recommendationViewModel: RecommendationViewModel = viewModel(
        factory = remember(engine) {
            object : ViewModelProvider.Factory {
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    Log.d("MainApp", "Creating RecommendationViewModel instance...")
                    @Suppress("UNCHECKED_CAST")
                    return RecommendationViewModel(engine!!) as T
                }
            }
        }
    )

    Surface(modifier = Modifier.fillMaxSize()) {
        when (currentScreen) {
            Screen.LOGIN -> LoginScreen(
                onNavigateToRegister = { currentScreen = Screen.REGISTER },
                onLoginSuccess = { currentScreen = Screen.HOME },
                authViewModel = authViewModel
            )
            Screen.REGISTER -> RegisterScreen(
                onNavigateToLogin = { currentScreen = Screen.LOGIN },
                onRegisterSuccess = { currentScreen = Screen.LOGIN }, // ZMIANA: Po rejestracji otwiera się okno logowania
                authViewModel = authViewModel
            )
            Screen.HOME -> HomeScreen(
                username = currentUsername ?: "użytkowniku",
                onNavigateToQuickRecommendation = {
                    recommendationViewModel.getQuickRecommendations(userProfile)
                    currentScreen = Screen.QUICK_RECOMMENDATION
                },
                onNavigateToSurvey = {
                    currentScreen = Screen.SURVEY
                },
                onNavigateToProfile = { currentScreen = Screen.PROFILE },
                onLogout = {
                    authViewModel.logout(onSuccess = { currentScreen = Screen.LOGIN })
                }
            )
            Screen.SURVEY -> SurveyScreen(
                authViewModel = authViewModel,
                recommendationViewModel = recommendationViewModel,
                onNavigateBack = { currentScreen = Screen.HOME },
                onNavigateToResults = { currentScreen = Screen.QUICK_RECOMMENDATION }
            )
            Screen.PROFILE -> ProfileScreen(
                onNavigateBack = { currentScreen = Screen.HOME },
                authViewModel = authViewModel
            )
            Screen.QUICK_RECOMMENDATION -> QuickRecommendationScreen(
                viewModel = recommendationViewModel,
                authViewModel = authViewModel,
                onBack = { currentScreen = Screen.HOME }
            )
        }
    }
}

@Composable
fun LoginScreen(
    onNavigateToRegister: () -> Unit,
    onLoginSuccess: () -> Unit,
    authViewModel: AuthViewModel
) {
    var loginOrEmail by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val context = LocalContext.current

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Zaloguj się", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(32.dp))
        OutlinedTextField(
            value = loginOrEmail,
            onValueChange = { loginOrEmail = it },
            label = { Text("Login lub Email") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Hasło") },
            modifier = Modifier.fillMaxWidth(),
            visualTransformation = PasswordVisualTransformation()
        )
        Spacer(Modifier.height(24.dp))
        Button(
            onClick = {
                authViewModel.loginUser(
                    loginOrEmail = loginOrEmail,
                    passwordInput = password,
                    onSuccess = {
                        Toast.makeText(context, "Zalogowano pomyślnie!", Toast.LENGTH_SHORT).show()
                        onLoginSuccess()
                    },
                    onError = { errorMessage ->
                        Toast.makeText(context, errorMessage, Toast.LENGTH_SHORT).show()
                    }
                )
            },
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("Zaloguj")
        }
        TextButton(onClick = onNavigateToRegister) {
            Text("Nie masz konta? Zarejestruj się")
        }
    }
}

@Composable
fun RegisterScreen(
    authViewModel: AuthViewModel,
    onNavigateToLogin: () -> Unit,
    onRegisterSuccess: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordConfirm by remember { mutableStateOf("") }

    var passwordVisible by remember { mutableStateOf(false) }
    var passwordConfirmVisible by remember { mutableStateOf(false) }

    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Stwórz nowe konto",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(Modifier.height(24.dp))

        OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            label = { Text("Login") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(Modifier.height(8.dp))

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )
        Spacer(Modifier.height(8.dp))

        // Hasło z przyciskiem tekstowym Pokaż/Ukryj
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Hasło") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
            trailingIcon = {
                TextButton(onClick = { passwordVisible = !passwordVisible }) {
                    Text(if (passwordVisible) "Ukryj" else "Pokaż", style = MaterialTheme.typography.labelMedium)
                }
            }
        )
        Spacer(Modifier.height(8.dp))

        // Powtórz hasło z przyciskiem tekstowym Pokaż/Ukryj
        OutlinedTextField(
            value = passwordConfirm,
            onValueChange = { passwordConfirm = it },
            label = { Text("Powtórz hasło") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = if (passwordConfirmVisible) VisualTransformation.None else PasswordVisualTransformation(),
            trailingIcon = {
                TextButton(onClick = { passwordConfirmVisible = !passwordConfirmVisible }) {
                    Text(if (passwordConfirmVisible) "Ukryj" else "Pokaż", style = MaterialTheme.typography.labelMedium)
                }
            }
        )
        Spacer(Modifier.height(24.dp))

        Button(
            onClick = {
                if (username.isBlank() || email.isBlank() || password.isBlank() || passwordConfirm.isBlank()) {
                    Toast.makeText(context, "Proszę uzupełnić wszystkie pola!", Toast.LENGTH_SHORT).show()
                    return@Button
                }

                if (password != passwordConfirm) {
                    Toast.makeText(context, "Podane hasła nie są identyczne!", Toast.LENGTH_SHORT).show()
                    return@Button
                }

                authViewModel.registerUser(
                    emailInput = email,
                    usernameInput = username,
                    passwordInput = password,
                    onSuccess = {
                        Toast.makeText(context, "Konto utworzone! Zaloguj się.", Toast.LENGTH_SHORT).show()
                        onRegisterSuccess()
                    },
                    onError = { errorMessage ->
                        Toast.makeText(context, errorMessage, Toast.LENGTH_SHORT).show()
                    }
                )
            },
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("Zarejestruj się", style = MaterialTheme.typography.titleMedium)
        }

        Spacer(Modifier.height(8.dp))

        TextButton(onClick = onNavigateToLogin) {
            Text("Masz już konto? Zaloguj się")
        }
    }
}
