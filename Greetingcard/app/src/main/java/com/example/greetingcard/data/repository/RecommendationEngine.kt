package com.example.greetingcard.data.repository

import android.util.Log
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.postgrest
import io.github.jan.supabase.postgrest.rpc
import io.github.jan.supabase.postgrest.query.Columns
import io.github.jan.supabase.postgrest.query.Order
import io.github.jan.supabase.postgrest.query.filter.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.InternalSerializationApi
import kotlinx.serialization.json.*
import com.example.greetingcard.data.model.RecipeRecommendation
import com.example.greetingcard.data.model.toCleanString
import com.example.greetingcard.UserProfile
import com.example.greetingcard.BuildConfig
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import org.json.JSONArray
import org.json.JSONObject
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.GenerateContentResponse

@OptIn(InternalSerializationApi::class)
@Serializable
private data class RecipeInsert(
    val name: String,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("prep_time") val prepTime: Int? = null,
    @SerialName("cook_time") val cookTime: Int? = null,
    @SerialName("total_time") val totalTime: Int? = null,
    val ingredients: JsonElement? = null,
    @SerialName("ingredient_names") val ingredientNames: JsonElement? = null,
    val instructions: JsonElement? = null,
    val tags: JsonElement? = null,
    val embedding: String? = null,
    val cuisine: String? = null,
    val warmth: Boolean? = null
)

@OptIn(InternalSerializationApi::class)
@Serializable
data class ExtractedPromptPrefs(
    val mustHaveIngredients: List<String> = emptyList(),
    val niceToHaveIngredients: List<String> = emptyList(),
    val excludedIngredients: List<String> = emptyList(),
    val niceToNotHaveIngredients: List<String> = emptyList(),
    val cuisines: List<String> = emptyList(),
    val diets: List<String> = emptyList(),
    val keywords: List<String> = emptyList()
)

@OptIn(InternalSerializationApi::class)
@Serializable
data class ExtractedReviewPrefs(
    val likedIngredients: List<String> = emptyList(),
    val dislikedIngredients: List<String> = emptyList(),
    val excludedIngredients: List<String> = emptyList()
)

@OptIn(InternalSerializationApi::class)
@Serializable
private data class ProfilePrefsUpdate(
    val liked_ingredients: List<String>,
    val disliked_ingredients: List<String>,
    val excluded_ingredients: List<String>
)

class RecommendationEngine(private val supabase: SupabaseClient) {

    private val apiKey = com.example.greetingcard.BuildConfig.GEMINI_API_KEY
    private val pollinationsKey = com.example.greetingcard.BuildConfig.POLLINATIONS_API_KEY

    private val primaryModel: GenerativeModel? by lazy {
        if (apiKey.isNotBlank()) GenerativeModel(modelName = "gemini-2.5-flash", apiKey = apiKey) else null
    }

    private val secondaryModel: GenerativeModel? by lazy {
        if (apiKey.isNotBlank()) GenerativeModel(modelName = "gemini-2.5-flash-lite", apiKey = apiKey) else null
    }

    private val tertiaryModel: GenerativeModel? by lazy {
        if (apiKey.isNotBlank()) GenerativeModel(modelName = "gemini-3.1-flash-lite", apiKey = apiKey) else null
    }

    private suspend fun safeGenerateContent(prompt: String, maxRetries: Int = 3): GenerateContentResponse? {
        // Próbujemy modeli w kolejności: 2.5 Flash -> 2.5 Flash-Lite -> 3.1 Flash-Lite
        val models = listOfNotNull(primaryModel, secondaryModel, tertiaryModel)
        if (models.isEmpty()) return null

        var lastException: Exception? = null

        for (model in models) {
            var currentRetry = 0
            while (currentRetry < maxRetries) {
                try {
                    Log.d("RecEngineAI", "Próba generowania (Model: ${model.modelName}, Próba: ${currentRetry + 1})")
                    return model.generateContent(prompt)
                } catch (e: Exception) {
                    lastException = e
                    val errorMsg = e.message ?: ""
                    
                    val isQuotaError = errorMsg.contains("429") || errorMsg.contains("Quota exceeded") || 
                                     errorMsg.contains("limit") || errorMsg.contains("exhausted")

                    if (isQuotaError) {
                        if (currentRetry < maxRetries - 1) {
                            currentRetry++
                            val waitTime = (1000L * currentRetry) + (300L..700L).random()
                            Log.w("RecEngineAI", "Limit przekroczony dla ${model.modelName}. Ponowna próba za ${waitTime}ms...")
                            delay(waitTime)
                        } else {
                            Log.e("RecEngineAI", "Model ${model.modelName} wyczerpał limity. Przełączam na następny model...")
                            break 
                        }
                    } else {
                        currentRetry++
                        delay(500L)
                    }
                }
            }
        }
        throw lastException ?: Exception("Wszystkie modele AI zawiodły po próbach")
    }

    companion object {
        private val tolerantJson = Json { 
            allowSpecialFloatingPointValues = true
            ignoreUnknownKeys = true 
            coerceInputValues = true
        }
    }

    @OptIn(InternalSerializationApi::class)
    @Serializable
    private data class RecipeVector(val embedding: JsonElement?) {
        fun parseToList(): List<Float>? {
            if (embedding == null) return null
            return try {
                when (embedding) {
                    is JsonPrimitive -> {
                        val content = embedding.content
                        if (content.isBlank() || content == "null") return null
                        content.removePrefix("[").removeSuffix("]").split(",")
                            .map { it.trim().toFloat() }
                    }
                    is JsonArray -> {
                        embedding.map { it.jsonPrimitive.content.toFloat() }
                    }
                    else -> null
                }
            } catch (e: Exception) { 
                Log.e("RecEngineVector", "Error parsing embedding: ${e.message}")
                null 
            }
        }
    }

    @OptIn(InternalSerializationApi::class)
    @Serializable
    private data class RecipeIdRow(val recipe_id: Long)

    suspend fun analyzeReviewNoteWithAI(note: String): ExtractedReviewPrefs {
        if (note.isBlank()) return ExtractedReviewPrefs()
        return try {
            Log.d("RecEngineProfile", "Analizuję tekst recenzji przez AI: \"$note\"")
            
            val systemInstruction = """
                Jesteś zaawansowanym analitykiem profili kulinarnych. Przeanalizuj komentarz/notatkę użytkownika po zjedzeniu posiłku i wyciągnij preferencje dotyczące konkretnych składników żywnościowych w formacie JSON.
                Zwróć WYŁĄCZNIE czysty obiekt JSON z tablicami tekstowymi dla kluczy:
                - "likedIngredients": składniki, które użytkownik chwali, polubił lub cieszy się, że były.
                - "dislikedIngredients": składniki, które mu nie smakowały, za którymi nie przepada lub deklaruje, że woli potrawy bez nich.
                - "excludedIngredients": alergie, nietolerancje powiązane medycznie.
                
                ZASADA FORMATOWANIA: Składniki zapisuj wyłącznie w mianowniku liczby pojedynczej, małymi literami. Jeśli brak informacji dla klucza, zwróć pustą tablicę [].
            """.trimIndent()

            val response = safeGenerateContent("$systemInstruction\n\nKomentarz użytkownika: \"$note\"")
            var responseText = response?.text ?: ""
            responseText = responseText.replace("```json", "").replace("```", "").trim()

            Log.d("RecEngineProfile", "AI przeanalizowało notatkę. Wynik JSON:\n$responseText")
            tolerantJson.decodeFromString<ExtractedReviewPrefs>(responseText)
        } catch (e: Exception) {
            Log.e("RecEngineProfile", "Błąd analizy notatki przez Gemini: ${e.message}")
            ExtractedReviewPrefs()
        }
    }

    suspend fun updateUserProfilePreferences(userId: String, updates: ExtractedReviewPrefs) {
        if (updates.likedIngredients.isEmpty() && updates.dislikedIngredients.isEmpty() && updates.excludedIngredients.isEmpty()) return
        try {
            Log.d("RecEngineProfile", "Pobieram aktualny profil z bazy w celu zmargowania tablic preferencji...")
            val currentProfile = supabase.postgrest["profiles"]
                .select {
                    filter {
                        eq("id", userId)
                    }
                }
                .decodeSingle<UserProfile>()

            val mergedLiked = ((currentProfile.liked_ingredients ?: emptyList()) + updates.likedIngredients)
                .map { it.lowercase().trim() }.filter { it.isNotBlank() }.distinct()

            val mergedDisliked = ((currentProfile.disliked_ingredients ?: emptyList()) + updates.dislikedIngredients)
                .map { it.lowercase().trim() }.filter { it.isNotBlank() }.distinct()

            val mergedExcluded = ((currentProfile.excluded_ingredients ?: emptyList()) + updates.excludedIngredients)
                .map { it.lowercase().trim() }.filter { it.isNotBlank() }.distinct()

            val updatePayload = ProfilePrefsUpdate(
                liked_ingredients = mergedLiked,
                disliked_ingredients = mergedDisliked,
                excluded_ingredients = mergedExcluded
            )

            supabase.postgrest["profiles"].update(updatePayload) {
                filter {
                    eq("id", userId)
                }
            }
            Log.d("RecEngineProfile", "Profil użytkownika został pomyślnie zaktualizowany!")
        } catch (e: Exception) {
            Log.e("RecEngineProfile", "Nie udało się zaktualizować profilu użytkownika: ${e.message}")
        }
    }

    suspend fun extractPreferencesFromPrompt(prompt: String): ExtractedPromptPrefs {
        if (prompt.isBlank()) return ExtractedPromptPrefs()
        return try {
            Log.d("RecEngineAI", "--- AI EXTRACTION START ---")
            Log.d("RecEngineAI", "Prompt użytkownika: \"$prompt\"")
            
            val systemInstruction = """
                Jesteś ekspertem analizy tekstu kulinarnym. Przeanalizuj zachciankę użytkownika i wyciągnij z niej informacje w formacie JSON.
                
                ZASADA UPROSZCZENIA SKŁADNIKÓW: Składniki sprowadzaj do ich najprostszej formy (np. "sos pomidorowy" -> 'pomidor', "szynka parmeńska" -> 'szynka', "ser parmezan" -> 'ser'). Chodzi o bazowy surowiec.
                
                KATEGORIE (BARDZO WAŻNE):
                1. "keywords": Główny temat/nazwa potrawy (np. 'gnocchi', 'pizza', 'zupa'). To jest baza dania.
                2. "diets": Wyłącznie diety (np. 'wegetariańska', 'wegańska', 'bez nabiału', 'keto').
                3. "mustHaveIngredients": Konkretne, dodatkowe składniki wymienione jako wymagane. Nie powtarzaj tu tego, co jest w 'keywords'.
                4. "niceToHaveIngredients": Składniki wspomniane jako opcjonalne lub lubiane.
                5. "excludedIngredients": Składniki zakazane.
                6. "niceToNotHaveIngredients": Składniki nielubiane.
                7. "cuisines": Kuchnie świata.
                
                FORMAT ODPOWIEDZI: Wyłącznie czysty JSON. Mianownik liczby pojedynczej, małe literery.
                Przykład dla "gnocchi z sosem pomidorowym i serem": {"keywords": ["gnocchi"], "diets": [], "mustHaveIngredients": ["pomidor"], "niceToHaveIngredients": ["ser"], "excludedIngredients": [], "niceToNotHaveIngredients": [], "cuisines": []}
            """.trimIndent()

            val response = safeGenerateContent("$systemInstruction\n\nTekst użytkownika: \"$prompt\"")
            var responseText = response?.text ?: ""
            Log.d("RecEngineAI", "Surowa odpowiedź AI: $responseText")
            
            responseText = responseText.replace("```json", "").replace("```", "").trim()
            
            val prefs = tolerantJson.decodeFromString<ExtractedPromptPrefs>(responseText)
            Log.d("RecEngineAI", "Sparsowane preferencje: $prefs")
            Log.d("RecEngineAI", "--- AI EXTRACTION END ---")
            prefs
        } catch (e: Exception) {
            Log.e("RecEngineAI", "Błąd podczas ekstrakcji preferencji: ${e.message}")
            ExtractedPromptPrefs()
        }
    }

    suspend fun getRecommendations(
        userId: String,
        historicalCentroidStr: String? = null,
        reqTags: List<String> = emptyList(),
        maxTime: Int? = null,
        isWarm: Boolean? = null,
        liked: List<String> = emptyList(),
        disliked: List<String> = emptyList(),
        allergies: List<String> = emptyList(),
        userPrompt: String? = null,
        extractedPrefs: ExtractedPromptPrefs
    ): List<RecipeRecommendation> = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        Log.d("RecEngineDB", "=== START REKOMENDACJI W VECTOR DB ===")
        val forbiddenIds = try { getForbiddenRecipeIds(userId) } catch(e: Exception) { emptySet<Long>() }

        val finalQueryEmbedding = if (!userPrompt.isNullOrBlank()) {
            generateEmbeddingForRecipe(userPrompt, extractedPrefs.mustHaveIngredients.joinToString(", "))
        } else {
            historicalCentroidStr
        } ?: "[${List(384) { "0.0" }.joinToString(",")}]"

        val combinedTags = (reqTags + extractedPrefs.diets + extractedPrefs.cuisines).distinct()
        val allExcluded = (extractedPrefs.excludedIngredients + allergies).map { it.lowercase().trim() }
        val finalReqIngredients = extractedPrefs.mustHaveIngredients.distinct()

        val userIsVegetarian = combinedTags.any { it.contains("wegetariańsk", ignoreCase = true) || it.contains("wegańsk", ignoreCase = true) }
        val meatWords = listOf("kurczak", "wołowina", "wieprzowina", "boczek", "kiełbasa", "szynka", "mięso", "indyk", "ryba", "łosoś")

        Log.d("RecEngineDB", "Parametry zapytania do bazy:")
        Log.d("RecEngineDB", " - Tagi: $combinedTags")
        Log.d("RecEngineDB", " - Wykluczone: $allExcluded")
        Log.d("RecEngineDB", " - Wymagane składniki: $finalReqIngredients")
        Log.d("RecEngineDB", " - Słowa kluczowe: ${extractedPrefs.keywords}")

        val filterLogic = { recipe: RecipeRecommendation ->
            val ingredientsStr = recipe.ingredientNames.toCleanString().lowercase()
            val recipeNameLower = recipe.name.lowercase()
            
            val hasMeat = userIsVegetarian && meatWords.any { meat -> ingredientsStr.contains(meat) || recipeNameLower.contains(meat) }
            val hasExcluded = allExcluded.any { excl -> ingredientsStr.contains(excl) || recipeNameLower.contains(excl) }
            val timeOk = maxTime == null || (recipe.totalTime ?: 0) <= maxTime
            val isForbidden = recipe.id > 0 && forbiddenIds.contains(recipe.id)

            val matchesWantedIngredients = finalReqIngredients.isEmpty() || finalReqIngredients.all { wanted ->
                val w = wanted.lowercase().trim()
                ingredientsStr.contains(w) || recipeNameLower.contains(w)
            }

            val matchesKeywords = extractedPrefs.keywords.isEmpty() || extractedPrefs.keywords.any { kw ->
                val k = kw.lowercase().trim()
                recipeNameLower.contains(k)
            }

            val passed = !hasMeat && !hasExcluded && timeOk && !isForbidden && matchesWantedIngredients && matchesKeywords
            if (!passed && (recipeNameLower.contains("gnocchi") || recipeNameLower.contains("makaron"))) {
                // Loguj dlaczego odrzucono potencjalnie interesujący przepis
                Log.v("RecEngineDB", "Odrzucono '${recipe.name}': Meat=$hasMeat, Excl=$hasExcluded, Time=$timeOk, MatchIng=$matchesWantedIngredients, MatchKW=$matchesKeywords")
            }
            passed
        }

        var rpcRecipes = try {
            val jsonParamsStrict = kotlinx.serialization.json.buildJsonObject {
                put("query_embedding", JsonPrimitive(finalQueryEmbedding))
                put("match_count", JsonPrimitive(100))
                put("req_tags", JsonArray(combinedTags.map { JsonPrimitive(it) }))
                put("excl_ing", JsonArray(allExcluded.map { JsonPrimitive(it) }))
                put("req_ing", JsonArray(finalReqIngredients.map { JsonPrimitive(it) }))
                put("max_time", maxTime?.let { JsonPrimitive(it) } ?: kotlinx.serialization.json.JsonNull)
                put("is_warm", isWarm?.let { JsonPrimitive(it) } ?: kotlinx.serialization.json.JsonNull)
            }

            val rawDataString = supabase.postgrest.rpc("match_recipes", jsonParamsStrict).data
            if (rawDataString == "null" || rawDataString.isBlank() || rawDataString == "[]") emptyList()
            else {
                tolerantJson.decodeFromString<List<RecipeRecommendation>>(rawDataString)
            }
        } catch (e: Exception) {
            Log.e("RecEngineDB", "Błąd RPC Strict: ${e.message}")
            emptyList()
        }

        if (rpcRecipes.isEmpty()) {
            Log.d("RecEngineDB", "Brak wyników dla Strict RPC. Próbuję Relaxed RPC...")
            rpcRecipes = try {
                val jsonParamsRelaxed = kotlinx.serialization.json.buildJsonObject {
                    put("query_embedding", JsonPrimitive(finalQueryEmbedding))
                    put("match_count", JsonPrimitive(100))
                    put("req_tags", JsonArray(emptyList()))
                    put("excl_ing", JsonArray(emptyList()))
                    put("req_ing", JsonArray(emptyList()))
                    put("max_time", maxTime?.let { JsonPrimitive(it) } ?: kotlinx.serialization.json.JsonNull)
                    put("is_warm", isWarm?.let { JsonPrimitive(it) } ?: kotlinx.serialization.json.JsonNull)
                }

                val rawDataString = supabase.postgrest.rpc("match_recipes", jsonParamsRelaxed).data
                if (rawDataString == "null" || rawDataString.isBlank() || rawDataString == "[]") emptyList()
                else kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Default) {
                    tolerantJson.decodeFromString<List<RecipeRecommendation>>(rawDataString)
                }
            } catch (e: Exception) {
                Log.e("RecEngineDB", "Błąd RPC Relaxed: ${e.message}")
                emptyList()
            }
        }

        val filteredRpcRecipes = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Default) {
            rpcRecipes.filter(filterLogic)
        }
        Log.d("RecEngineDB", "Wyniki z bazy (RPC): surowe=${rpcRecipes.size}, po filtracji=${filteredRpcRecipes.size}")

        val accumulativeDbRecipes = filteredRpcRecipes.toMutableList()

        if (accumulativeDbRecipes.size < 7) {
            Log.d("RecEngineDB", "Mniej niż 7 potraw po RPC. Pobieram fallback z bazy...")
            try {
                val rawSelectData = supabase.postgrest["recipes"].select { limit(1000) }.data
                val globalRecipes = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Default) {
                    tolerantJson.decodeFromString<List<RecipeRecommendation>>(rawSelectData)
                }
                val filteredGlobalRecipes = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Default) {
                    globalRecipes.filter(filterLogic)
                }

                for (recipe in filteredGlobalRecipes) {
                    if (accumulativeDbRecipes.size >= 7) break
                    if (accumulativeDbRecipes.none { it.id == recipe.id }) {
                        accumulativeDbRecipes.add(recipe)
                    }
                }
                Log.d("RecEngineDB", "Po dobraniu fallbacku z DB mamy ${accumulativeDbRecipes.size} potraw.")
            } catch (e: Exception) {
                Log.e("RecEngineDB", "Błąd przy pobieraniu fallbacku z DB: ${e.message}")
            }
        }

        val filteredDbRecipes = accumulativeDbRecipes.take(7)
        val targetAiCount = 10 - filteredDbRecipes.size
        Log.d("RecEngineAI", "Z bazy wybrano ostatecznie: ${filteredDbRecipes.size} szt. Potrzeba z AI: $targetAiCount")
        
        val aiRecipes = try {
            if (targetAiCount > 0) {
                fetchAIRecipes(
                    liked = liked, 
                    disliked = disliked, 
                    allergies = allergies, 
                    surveyWanted = finalReqIngredients, 
                    violenceClearExcl = allExcluded, 
                    maxTime = maxTime, 
                    isWarm = isWarm, 
                    count = targetAiCount, 
                    excludedNames = filteredDbRecipes.map { it.name }, 
                    userPrompt = userPrompt,
                    diets = combinedTags
                )
            } else emptyList<RecipeRecommendation>()
        } catch (e: Exception) {
            Log.e("RecEngineAI", "Błąd fetchAIRecipes: ${e.message}")
            emptyList<RecipeRecommendation>()
        }

        val finalRecipes = mutableListOf<RecipeRecommendation>()
        finalRecipes.addAll(filteredDbRecipes)
        finalRecipes.addAll(aiRecipes)
        
        if (finalRecipes.size < 10) {
            Log.d("RecEngineSummary", "Wciąż brakuje przepisów, dobieram dowolne (awaryjnie)...")
            try {
                val rawSelectData = supabase.postgrest["recipes"].select { limit(50) }.data
                val globalRecipes = tolerantJson.decodeFromString<List<RecipeRecommendation>>(rawSelectData)
                val safetyRecipes = globalRecipes.filter { r -> !forbiddenIds.contains(r.id) }
                for (recipe in safetyRecipes) {
                    if (finalRecipes.size >= 10) break
                    if (finalRecipes.none { it.id == recipe.id }) finalRecipes.add(recipe)
                }
            } catch (e: Exception) {}
        }

        applyReRanking(finalRecipes, forbiddenIds, liked + extractedPrefs.niceToHaveIngredients, disliked + extractedPrefs.niceToNotHaveIngredients)
    }

    private suspend fun fetchAIRecipes(
        liked: List<String>, disliked: List<String>, allergies: List<String>,
        surveyWanted: List<String>, violenceClearExcl: List<String>, maxTime: Int?, isWarm: Boolean?, count: Int,
        excludedNames: List<String> = emptyList(),
        userPrompt: String? = null,
        diets: List<String> = emptyList()
    ): List<RecipeRecommendation> {
        Log.d("RecEngineAI", "=== START GENEROWANIA AI (Count: $count) ===")
        val aiRecipes = mutableListOf<RecipeRecommendation>()

        val dietsStr = if (diets.isNotEmpty()) diets.joinToString(", ") else "standardowa"
        var dietPrompt = "Dieta: $dietsStr. Składniki mile widziane: ${surveyWanted.joinToString(", ")}."
        if (!userPrompt.isNullOrBlank()) {
            dietPrompt += "\nUżytkownik opisał swoją zachciankę bezpośrednio tak: \"$userPrompt\". Spełnij te kryteria w pierwszej kolejności!"
        }
        
        val prompt = "$dietPrompt\n\n" +
                "Wymyśl dokładnie $count przepisów kulinarnych W JĘZYKU POLSKIM pasujących do wymagań.\n" +
                "Odpowiedz WYŁĄCZNIE jako czysta tablica JSON zawierająca dokładnie $count obiektów.\n" +
                "Format potrawy:\n" +
                "{\"name\": \"Nazwa\", \"prepTime\": 15, \"cookTime\": 15, \"totalTime\": 30, \"cuisine\": \"Włoska\", \"warmth\": true, \"tags\": [\"vegetarian\"], \"ingredients\": [{\"name\": \"składnik\", \"amount\": \"100\", \"unit\": \"g\"}], \"ingredientNames\": [\"składnik\"], \"instructions\": [\"Krok 1...\"]}"

        val response = safeGenerateContent(prompt)
        var responseText = response?.text ?: ""
        responseText = responseText.replace("```json", "").replace("```", "").trim()

        if (responseText.isNotEmpty()) {
            try {
                val jsonArray = JSONArray(responseText)
                for (i in 0 until jsonArray.length()) {
                    val obj = jsonArray.getJSONObject(i)
                    val rawName = obj.optString("name", "Przepis AI")
                    val ingNamesArray = obj.optJSONArray("ingredientNames")
                    val ingNamesJson = JsonArray(List(ingNamesArray?.length() ?: 0) { j -> JsonPrimitive(ingNamesArray!!.optString(j)) })
                    val instArray = obj.optJSONArray("instructions")
                    val instructionsList = mutableListOf<String>()
                    if (instArray != null) for (j in 0 until instArray.length()) instructionsList.add("${j + 1}. ${instArray.optString(j)}")
                    val instructionsJson = JsonPrimitive(instructionsList.joinToString("\n"))
                    val rawIngredientsStr = obj.optJSONArray("ingredients")?.toString() ?: "[]"

                    aiRecipes.add(
                        RecipeRecommendation(
                            id = -(i + 1L + System.currentTimeMillis() % 10000),
                            name = "$rawName ✨ (Przepis AI)",
                            imageUrl = null,
                            prepTime = obj.optInt("prepTime"),
                            cookTime = obj.optInt("cookTime"),
                            totalTime = obj.optInt("totalTime"),
                            ingredients = tolerantJson.parseToJsonElement(rawIngredientsStr),
                            ingredientNames = ingNamesJson,
                            instructions = instructionsJson,
                            tags = JsonArray(emptyList()),
                            cuisine = obj.optString("cuisine", "Międzynarodowa"),
                            warmth = obj.optBoolean("warmth", true),
                            similarity = 0.5f
                        )
                    )
                }
            } catch (e: Exception) {
                Log.e("RecEngineAI", "Błąd parsowania JSON AI: ${e.message}")
            }
        }
        return aiRecipes
    }

    suspend fun calculateCentroid(userId: String): List<Float>? {
        return try {
            val likedReviews = supabase.postgrest["recipe_reviews"]
                .select(columns = Columns.list("recipe_id")) {
                    filter {
                        eq("profile_id", userId)
                        gte("rating", 4)
                    }
                    order("created_at", Order.DESCENDING)
                    limit(10)
                }
                .decodeList<RecipeIdRow>()
            if (likedReviews.isEmpty()) return null
            val recipeIds = likedReviews.map { it.recipe_id }
            val vectors = supabase.postgrest["recipes"]
                .select(columns = Columns.list("embedding")) {
                    filter {
                        isIn("id", recipeIds)
                    }
                }
                .decodeList<RecipeVector>().mapNotNull { it.parseToList() }
            if (vectors.isEmpty()) return null
            val dimension = vectors.first().size
            val centroid = MutableList(dimension) { 0.0f }
            for (v in vectors) for (i in 0 until dimension) centroid[i] += v[i]
            for (i in 0 until dimension) centroid[i] = centroid[i] / vectors.size.toFloat()
            return centroid
        } catch (e: Exception) { null }
    }

    private suspend fun getForbiddenRecipeIds(userId: String): Set<Long> {
        return try {
            supabase.postgrest["recipe_reviews"]
                .select(columns = Columns.list("recipe_id")) {
                    filter {
                        eq("profile_id", userId)
                        lte("rating", 3)
                    }
                }
                .decodeList<RecipeIdRow>().map { it.recipe_id }.toSet()
        } catch (e: Exception) { emptySet() }
    }

    private fun applyReRanking(candidates: List<RecipeRecommendation>, forbiddenIds: Set<Long>, liked: List<String>, disliked: List<String>): List<RecipeRecommendation> {
        val refinedList = mutableListOf<RecipeRecommendation>()
        for (recipe in candidates) {
            if (recipe.id > 0 && forbiddenIds.contains(recipe.id)) continue
            var scoreModifier = 0.0f
            val recipeIngredients = recipe.ingredientNames.toCleanString().lowercase()
            for (like in liked) if (like.isNotBlank() && recipeIngredients.contains(like.lowercase().trim())) scoreModifier += 0.5f
            for (dislike in disliked) if (dislike.isNotBlank() && recipeIngredients.contains(dislike.lowercase().trim())) scoreModifier -= 1.0f
            val baseSimilarity = if (recipe.id < 0) 0.5f else recipe.similarity
            recipe.adjustedScore = (baseSimilarity * 10.0f) + scoreModifier
            refinedList.add(recipe)
        }
        return refinedList.sortedByDescending { it.adjustedScore }.take(10)
    }

    suspend fun generateImageForRecipe(recipeName: String, ingredients: String? = null): String? {
        val cleanName = recipeName.replace(" ✨ (Przepis AI)", "").trim()

        // 1. Tłumaczenie na angielski (niezbędne dla jakości i stabilności AI)
        val englishName = try {
            val response = safeGenerateContent("Translate this food name to English (ONLY the name): \"$cleanName\"")
            response?.text?.trim()?.removeSurrounding("\"")?.removeSuffix(".") ?: cleanName
        } catch (e: Exception) { cleanName }

        Log.d("RecEngine", "Pollinations Prompt: $englishName")

        // 2. Link Pollinations (Standard 2026: gen.pollinations.ai z parametrem 'key')
        val safePrompt = java.net.URLEncoder.encode("Professional food photography of $englishName, gourmet presentation, highly detailed, 4k", "UTF-8")

        // W 2026 klucz API podaje się w parametrze 'key'.
        // Używamy zunifikowanego endpointu 'gen.pollinations.ai/image/'
        val finalUrl = "https://gen.pollinations.ai/image/$safePrompt?width=1024&height=1024&nologo=true&model=flux&seed=${(1..1000000).random()}&key=${BuildConfig.POLLINATIONS_API_KEY}"

        Log.d("RecEngine", "Wygenerowany URL Pollinations (Key-Auth): ${finalUrl.replace(BuildConfig.POLLINATIONS_API_KEY, "***")}")
        return finalUrl
    }

    suspend fun saveRecipeToDatabase(recipe: RecipeRecommendation): RecipeRecommendation {
        val insertData = RecipeInsert(
            name = recipe.name, imageUrl = recipe.imageUrl, prepTime = recipe.prepTime,
            cookTime = recipe.cookTime, totalTime = recipe.totalTime, ingredients = recipe.ingredients,
            ingredientNames = recipe.ingredientNames, instructions = recipe.instructions, tags = recipe.tags,
            embedding = recipe.embedding, cuisine = recipe.cuisine, warmth = recipe.warmth
        )
        return supabase.postgrest["recipes"].insert(insertData) { select() }.decodeSingle<RecipeRecommendation>()
    }

    suspend fun saveRatingToDatabase(userId: String, recipeId: Long, rating: Int) {
        val review = com.example.greetingcard.RecipeReviewUpsert(profile_id = userId, recipe_id = recipeId, rating = rating)
        supabase.postgrest["recipe_reviews"].upsert(value = review, onConflict = "profile_id,recipe_id")
    }

    suspend fun generateEmbeddingForRecipe(name: String, ingredients: String): String? {
        return try {
            val prompt = "Wygeneruj wektor embedding (384 liczby zmiennoprzecinkowe) dla: $name. Odpowiedz WYŁĄCZNIE tablicą liczb w [], np. [0.1, -0.2]."
            val response = safeGenerateContent(prompt)
            var resultText = response?.text?.trim() ?: ""
            resultText = resultText.replace("```json", "").replace("```", "").trim()
            if (resultText.startsWith("[") && resultText.endsWith("]")) {
                val rawNumbers = resultText.removePrefix("[").removeSuffix("]").split(",")
                val floats = rawNumbers.map { it.trim().toFloatOrNull() ?: 0.0f }
                val standardDimensions = if (floats.size >= 384) floats.take(384) else floats + List(384 - floats.size) { 0.0f }
                standardDimensions.joinToString(prefix = "[", postfix = "]", separator = ",")
            } else null
        } catch (e: Exception) { null }
    }
}
