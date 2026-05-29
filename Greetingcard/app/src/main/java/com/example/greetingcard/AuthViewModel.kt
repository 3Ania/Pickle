package com.example.greetingcard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import io.github.jan.supabase.gotrue.auth
import io.github.jan.supabase.gotrue.providers.builtin.Email
import io.github.jan.supabase.postgrest.postgrest
import io.github.jan.supabase.postgrest.rpc
import io.github.jan.supabase.postgrest.query.filter.*
import io.github.jan.supabase.postgrest.query.Columns
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import android.util.Log

@Serializable
data class UsernameUpdate(val username: String)

// DODANE: Klasa służąca do aktualizowania list preferencji
@Serializable
data class PreferencesUpdate(
    val excluded_ingredients: List<String>,
    val disliked_ingredients: List<String>,
    val liked_ingredients: List<String>,
    val diets: List<String>
)

class AuthViewModel : ViewModel() {

    private val _currentUsername = MutableStateFlow<String?>(null)
    val currentUsername: StateFlow<String?> = _currentUsername

    private val _currentEmail = MutableStateFlow<String?>(null)
    val currentEmail: StateFlow<String?> = _currentEmail

    // DODANE: Trzymamy CAŁY pobrany profil użytkownika, żeby widok mógł z niego odczytać początkowe listy
    private val _userProfile = MutableStateFlow<UserProfile?>(null)
    val userProfile: StateFlow<UserProfile?> = _userProfile

    init {
        Log.d("AuthVM", "AuthViewModel initialized. Starting session check...")
        checkSession()
    }

    fun checkSession() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val session = SupabaseInstance.client.auth.currentSessionOrNull()
                if (session != null) {
                    val user = session.user
                    val email = user?.email
                    if (_currentEmail.value != email) {
                        _currentEmail.value = email
                    }
                    fetchUsername(user?.id)
                }
            } catch (e: Exception) {
                Log.e("AuthVM", "Błąd sprawdzania sesji: ${e.message}")
                _currentUsername.value = null
                _currentEmail.value = null
                _userProfile.value = null
            }
        }
    }

    fun loginUser(loginOrEmail: String, passwordInput: String, onSuccess: () -> Unit, onError: (String) -> Unit) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val finalEmail = if (loginOrEmail.contains("@")) {
                    loginOrEmail
                } else {
                    val emailFromDb = try {
                        val response = SupabaseInstance.client.postgrest.rpc(
                            function = "get_user_email",
                            parameters = buildJsonObject {
                                put("p_username", loginOrEmail)
                            }
                        )
                        response.decodeAs<String>()
                    } catch (e: Exception) {
                        null
                    }

                    if (emailFromDb == null) {
                        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                            onError("Nie znaleziono użytkownika o podanym loginie.")
                        }
                        return@launch
                    }
                    emailFromDb
                }

                SupabaseInstance.client.auth.signInWith(Email) {
                    this.email = finalEmail
                    this.password = passwordInput
                }

                val user = SupabaseInstance.client.auth.currentUserOrNull()
                _currentEmail.value = user?.email
                fetchUsername(user?.id)
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onSuccess()
                }
            } catch (e: Exception) {
                e.printStackTrace()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onError("Błąd logowania: Niepoprawne dane lub problem z siecią.")
                }
            }
        }
    }

    fun registerUser(
        emailInput: String,
        usernameInput: String,
        passwordInput: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val existingUsers = SupabaseInstance.client.postgrest["profiles"]
                    .select {
                        filter {
                            eq("username", usernameInput)
                        }
                    }
                    .decodeList<UserProfile>()

                if (existingUsers.isNotEmpty()) {
                    kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                        onError("Ten login jest już zajęty!")
                    }
                    return@launch
                }

                SupabaseInstance.client.auth.signUpWith(Email) {
                    this.email = emailInput
                    this.password = passwordInput
                }

                val user = SupabaseInstance.client.auth.currentUserOrNull()
                    ?: SupabaseInstance.client.auth.retrieveUserForCurrentSession(updateSession = true)
                val userId = user.id

                val profile = UserProfile(id = userId, username = usernameInput)
                SupabaseInstance.client.postgrest["profiles"].insert(profile)

                SupabaseInstance.client.auth.signOut()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onSuccess()
                }

            } catch (e: Exception) {
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onError("Błąd rejestracji. Sprawdź, czy email nie jest już zajęty.")
                }
                e.printStackTrace()
            }
        }
    }

    fun logout(onSuccess: () -> Unit) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            SupabaseInstance.client.auth.signOut()
            _currentUsername.value = null
            _currentEmail.value = null
            _userProfile.value = null
            kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                onSuccess()
            }
        }
    }

    private suspend fun fetchUsername(userId: String?) {
        if (userId == null) return

        val profiles = SupabaseInstance.client.postgrest["profiles"]
            .select {
                filter {
                    eq("id", userId)
                }
            }
            .decodeList<UserProfile>()

        val profile = profiles.firstOrNull()
        _currentUsername.value = profile?.username
        _userProfile.value = profile // Zapisujemy profil w stanie, żeby preferences mogło z niego odczytać
    }

    fun updateEmail(newEmail: String, onResult: (Boolean, String) -> Unit) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                SupabaseInstance.client.auth.updateUser {
                    this.email = newEmail
                }
                _currentEmail.value = newEmail
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(true, "Zaktualizowano email pomyślnie.")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(false, "Błąd zmiany emaila: ${e.message}")
                }
            }
        }
    }

    fun updateUsername(newUsername: String, onResult: (Boolean, String) -> Unit) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val user = SupabaseInstance.client.auth.currentUserOrNull() ?: throw Exception("Brak sesji")
                val userId = user.id

                val existingUsers = SupabaseInstance.client.postgrest["profiles"]
                    .select {
                        filter {
                            eq("username", newUsername)
                        }
                    }
                    .decodeList<UserProfile>()

                if (existingUsers.isNotEmpty() && existingUsers.first().id != userId) {
                    kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                        onResult(false, "Ten login jest już zajęty!")
                    }
                    return@launch
                }

                SupabaseInstance.client.postgrest["profiles"].update(UsernameUpdate(newUsername)) {
                    filter {
                        eq("id", userId)
                    }
                }

                _currentUsername.value = newUsername
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(true, "Zaktualizowano login pomyślnie.")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(false, "Błąd zmiany loginu: ${e.message}")
                }
            }
        }
    }

    fun updatePassword(newPassword: String, onResult: (Boolean, String) -> Unit) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                SupabaseInstance.client.auth.updateUser {
                    this.password = newPassword
                }
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(true, "Zaktualizowano hasło pomyślnie.")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(false, "Błąd zmiany hasła. Może być za krótkie.")
                }
            }
        }
    }

    // DODANE: Funkcja do zapisywania diet i składników w bazie danych
    fun updatePreferences(
        excluded: List<String>,
        disliked: List<String>,
        liked: List<String>,
        diets: List<String>,
        onResult: (Boolean, String) -> Unit
    ) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val user = SupabaseInstance.client.auth.currentUserOrNull() ?: throw Exception("Brak sesji")
                val userId = user.id
                val updateData = PreferencesUpdate(excluded, disliked, liked, diets)

                SupabaseInstance.client.postgrest["profiles"].update(updateData) {
                    filter {
                        eq("id", userId)
                    }
                }

                // Aktualizujemy też stan lokalny, żeby interfejs nie migał
                _userProfile.value = _userProfile.value?.copy(
                    excluded_ingredients = excluded,
                    disliked_ingredients = disliked,
                    liked_ingredients = liked,
                    diets = diets
                )
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(true, "Zapisano preferencje")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) {
                    onResult(false, "Błąd zapisu preferencji: ${e.message}")
                }
            }
        }
    }
}
