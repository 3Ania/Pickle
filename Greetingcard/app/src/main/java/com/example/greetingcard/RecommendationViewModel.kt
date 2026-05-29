package com.example.greetingcard

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.greetingcard.data.model.RecipeRecommendation
import com.example.greetingcard.UserProfile
import com.example.greetingcard.data.model.toCleanString
import com.example.greetingcard.data.repository.RecommendationEngine
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable

// --- PRZYWRÓCONO: KLASYCZNA REPREZENTACJA REVIEWS (BEZ NOTATKI DO BAZY) ---
@Serializable
data class RecipeReviewUpsert(val profile_id: String, val recipe_id: Long, val rating: Int)

sealed interface RecommendationUiState {
    object Idle : RecommendationUiState
    object Loading : RecommendationUiState
    data class Success(val recipes: List<RecipeRecommendation>) : RecommendationUiState
    data class Error(val message: String) : RecommendationUiState
}

class RecommendationViewModel(
    private val engine: RecommendationEngine
) : ViewModel() {

    private val _uiState = MutableStateFlow<RecommendationUiState>(RecommendationUiState.Idle)
    val uiState: StateFlow<RecommendationUiState> = _uiState
    private val _selectedRecipe = MutableStateFlow<RecipeRecommendation?>(null)
    val selectedRecipe: StateFlow<RecipeRecommendation?> = _selectedRecipe

    private var currentJob: kotlinx.coroutines.Job? = null

    fun getQuickRecommendations(
        profile: UserProfile?,
        userPrompt: String = "",
        maxTime: Int? = null,
        isWarm: Boolean? = null
    ) {
        if (profile == null) return
        if (_uiState.value is RecommendationUiState.Loading) return

        currentJob?.cancel()
        currentJob = viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            _uiState.value = RecommendationUiState.Loading
            try {
                Log.d("RecVM", "Przetwarzam zapytanie tekstowe za pomocą AI...")
                val extractedPrefs = engine.extractPreferencesFromPrompt(userPrompt)

                val likedIngredients = (profile.liked_ingredients ?: emptyList())
                val dislikedIngredients = (profile.disliked_ingredients ?: emptyList())
                val allergies = emptyList<String>()
                val profileDiets = (profile.diets ?: emptyList())

                val centroid = engine.calculateCentroid(profile.id)
                val centroidStr = centroid?.joinToString(prefix = "[", postfix = "]", separator = ",")

                val list = engine.getRecommendations(
                    userId = profile.id,
                    historicalCentroidStr = centroidStr,
                    reqTags = profileDiets,
                    maxTime = maxTime,
                    isWarm = isWarm,
                    liked = likedIngredients,
                    disliked = dislikedIngredients,
                    allergies = allergies,
                    userPrompt = userPrompt,
                    extractedPrefs = extractedPrefs
                )
                _uiState.value = RecommendationUiState.Success(list)
            } catch (e: Exception) {
                Log.e("RecVM", "Błąd pobierania rekomendacji: ${e.message}", e)
                val userFriendlyMessage = when {
                    e is kotlinx.coroutines.CancellationException -> "Anulowano zapytanie."
                    e.message?.contains("Unable to resolve host") == true -> "Brak połączenia z internetem."
                    else -> "Błąd: ${e.message ?: "Nieznany problem"}"
                }
                _uiState.value = RecommendationUiState.Error(userFriendlyMessage)
            } finally {
                currentJob = null
            }
        }
    }

    fun selectRecipe(recipe: RecipeRecommendation) {
        _selectedRecipe.value = recipe
    }

    fun resetSelection() {
        _selectedRecipe.value = null
    }

    fun generateImageForSelectedRecipe(recipe: RecipeRecommendation) {
        if (!recipe.imageUrl.isNullOrBlank() && !recipe.imageUrl.contains("flaticon")) return
        updateImageLoadingState(recipe.id, true)
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val ingredientsStr = recipe.ingredientNames.toCleanString()
                val url = engine.generateImageForRecipe(recipe.name, ingredientsStr)
                if (url != null) {
                    applyNewImageUrl(recipe.id, url)
                } else {
                    updateImageLoadingState(recipe.id, false)
                }
            } catch (e: Exception) {
                updateImageLoadingState(recipe.id, false)
            }
        }
    }

    fun startImageGenerationForRecipe(recipe: RecipeRecommendation) {
        generateImageForSelectedRecipe(recipe)
    }

    // --- ROZBUDOWANA FUNKCJA ZAPISU (POPRAWIONY PROBLEM KLUCZA OBCEGO) ---
    fun finalizeAndSaveAiRecipe(
        userId: String,
        recipe: RecipeRecommendation,
        rating: Int,
        note: String? = null,
        onImmediateDismiss: () -> Unit
    ) {
        onImmediateDismiss()
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                var finalRecipeId = recipe.id

                if (recipe.id < 0) {
                    val cleanName = recipe.name.replace(" ✨ (Przepis AI)", "")
                    if (rating >= 4) {
                        Log.d("RecVM", ">>> TŁO: Przepis AI oceniony wysoko ($rating/5). Rozpoczynam procedurę trwałego zapisu...")
                        val calculatedEmbedding = engine.generateEmbeddingForRecipe(cleanName, recipe.ingredients?.toString() ?: "")
                        val recipeToSave = recipe.copy(
                            id = 0,
                            name = cleanName,
                            embedding = calculatedEmbedding
                        )
                        val insertedRecipe = engine.saveRecipeToDatabase(recipeToSave)
                        finalRecipeId = insertedRecipe.id
                    } else {
                        Log.w("RecVM", ">>> TŁO: Przepis AI oceniony słabo ($rating/5). Pomijam zapis w ogólnej tabeli 'recipes'.")
                    }
                }

                // Zapisujemy samą ocenę gwiazdkową TYLKO wtedy, gdy przepis faktycznie istnieje w bazie danych (ID > 0)
                if (finalRecipeId > 0) {
                    Log.d("RecVM", ">>> TŁO: Zapisuję ocenę $rating/5 dla przepisu ID: $finalRecipeId w bazie SQL.")
                    engine.saveRatingToDatabase(userId, finalRecipeId, rating)
                } else {
                    Log.w("RecVM", ">>> TŁO: Pomijam zapis relacyjny gwiazdek w tabeli 'recipe_reviews', ponieważ przepis AI z niską oceną nie istnieje w bazie danych.")
                }

                // NOTATKA JEST ZAWSZE ANALIZOWANA (nawet jeśli przepis nie został zapisany na stałe w bazie potraw!)
                if (!note.isNullOrBlank()) {
                    Log.d("RecVM", ">>> TŁO: Wykryto notatkę recenzji. Uruchamiam analizę profilu kulinarnego przez Gemini...")
                    val extractedReviewPrefs = engine.analyzeReviewNoteWithAI(note)
                    engine.updateUserProfilePreferences(userId, extractedReviewPrefs)
                }

            } catch (e: Exception) {
                Log.e("RecVM", ">>> TŁO BŁĄD: Krytyczna awaria operacji zapisu i aktualizacji profilu: ${e.message}")
            }
        }
    }

    private fun updateImageLoadingState(recipeId: Long, isLoading: Boolean) {
        val currentState = _uiState.value
        if (currentState is RecommendationUiState.Success) {
            val newList = currentState.recipes.map {
                if (it.id == recipeId) it.copy(isImageLoading = isLoading) else it
            }
            _uiState.value = RecommendationUiState.Success(newList)
        }
        _selectedRecipe.value?.let {
            if (it.id == recipeId) _selectedRecipe.value = it.copy(isImageLoading = isLoading)
        }
    }

    private fun applyNewImageUrl(recipeId: Long, url: String) {
        val currentState = _uiState.value
        if (currentState is RecommendationUiState.Success) {
            val newList = currentState.recipes.map {
                if (it.id == recipeId) it.copy(imageUrl = url, isImageLoading = false) else it
            }
            _uiState.value = RecommendationUiState.Success(newList)
        }
        _selectedRecipe.value?.let {
            if (it.id == recipeId) _selectedRecipe.value = it.copy(imageUrl = url, isImageLoading = false)
        }
    }
}
