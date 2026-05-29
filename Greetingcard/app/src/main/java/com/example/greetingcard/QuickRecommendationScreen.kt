package com.example.greetingcard

import android.util.Log
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.example.greetingcard.data.model.RecipeRecommendation
import com.example.greetingcard.data.model.toCleanString
import org.json.JSONArray
import org.json.JSONObject
import kotlinx.serialization.json.jsonPrimitive

import coil.compose.SubcomposeAsyncImage
import coil.request.ImageRequest
import androidx.compose.ui.platform.LocalContext

// --- PROFESJONALNA FUNKCJA FORMATOWANIA: Obsługuje obiekty JsonElement oraz tradycyjne Stringi ---
fun formatListText(raw: Any?): String {
    if (raw == null) return "Brak danych"

    // Obsługa nowego formatu obiektowego JsonElement (pochodzącego z generatora AI)
    if (raw is kotlinx.serialization.json.JsonElement) {
        if (raw is kotlinx.serialization.json.JsonArray) {
            val list = mutableListOf<String>()
            for (element in raw) {
                if (element is kotlinx.serialization.json.JsonObject) {
                    val name = element["name"]?.jsonPrimitive?.content ?: ""
                    val amount = element["amount"]?.jsonPrimitive?.content ?: ""
                    val unit = element["unit"]?.jsonPrimitive?.content ?: ""
                    val capitalizedName = name.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
                    val amountUnit = listOf(amount, unit).filter { it.isNotBlank() && it != "null" }.joinToString(" ")
                    val line = if (amountUnit.isNotEmpty()) "$capitalizedName - $amountUnit" else capitalizedName
                    if (line.isNotBlank()) list.add("• $line")
                } else if (element is kotlinx.serialization.json.JsonPrimitive) {
                    val content = element.content.trim()
                    if (content.isNotBlank()) {
                        val capitalized = content.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
                        list.add("• $capitalized")
                    }
                }
            }
            if (list.isNotEmpty()) return list.joinToString("\n")
        }
        val cleanText = raw.toCleanString().trim()
        if (cleanText.startsWith("[")) {
            return formatListText(cleanText)
        }
        return cleanText
    }

    // Tradycyjna obsługa dla surowych Stringów tekstowych z bazy danych
    val text = raw.toString().trim()
    if (text.isBlank() || text == "null") return "Brak danych"

    if (text.startsWith("[")) {
        try {
            val arr = JSONArray(text)
            val list = mutableListOf<String>()
            for (i in 0 until arr.length()) {
                val item = arr.get(i)
                if (item is JSONObject) {
                    val name = item.optString("name", "").trim()
                    val amount = item.optString("amount", "").trim()
                    val unit = item.optString("unit", "").trim()
                    if (name.isNotEmpty()) {
                        val capitalizedName = name.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
                        val amountUnit = listOf(amount, unit).filter { it.isNotBlank() && it != "null" }.joinToString(" ")
                        val line = if (amountUnit.isNotEmpty()) "$capitalizedName - $amountUnit" else capitalizedName
                        list.add("• $line")
                    }
                } else {
                    val strItem = arr.optString(i, "").trim()
                    if (strItem.isNotBlank()) {
                        val capitalized = strItem.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
                        list.add("• $capitalized")
                    }
                }
            }
            if (list.isNotEmpty()) return list.joinToString("\n")
        } catch (e: Exception) {}
    }

    if (text.contains("\n")) {
        return text.split("\n").map { it.trim() }.filter { it.isNotBlank() }.joinToString("\n") { if (it.startsWith("•")) it else "• $it" }
    }
    if (text.contains(",")) {
        return text.split(",").map { it.trim() }.filter { it.isNotBlank() }.joinToString("\n") { "• ${it.replaceFirstChar { c -> if (c.isLowerCase()) c.titlecase() else c.toString() }}" }
    }
    return if (text.startsWith("•")) text else "• $text"
}

@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
fun QuickRecommendationScreen(
    viewModel: RecommendationViewModel,
    authViewModel: AuthViewModel,
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val selectedRecipe by viewModel.selectedRecipe.collectAsState()
    val userProfile by authViewModel.userProfile.collectAsState()

    if (selectedRecipe != null) {
        CookingModeScreen(
            recipe = selectedRecipe!!,
            viewModel = viewModel,
            onBack = { viewModel.resetSelection() },
            onFinish = { _, rating, note ->
                Log.d("RecUI", "Zamykam natychmiast widok. Zapis przeniesiony do operacji w tle.")
                if (userProfile != null) {
                    viewModel.finalizeAndSaveAiRecipe(
                        userId = userProfile!!.id,
                        recipe = selectedRecipe!!,
                        rating = rating,
                        note = note,
                        onImmediateDismiss = {
                            viewModel.resetSelection()
                            onBack()
                        }
                    )
                } else {
                    viewModel.resetSelection()
                    onBack()
                }
            }
        )
    } else {
        Scaffold(
            topBar = {
                CenterAlignedTopAppBar(
                    title = { Text("Polecane dla Ciebie") },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Wróć")
                        }
                    }
                )
            }
        ) { padding ->
            when (uiState) {
                is RecommendationUiState.Loading -> Box(Modifier.fillMaxSize().padding(padding), Alignment.Center) { CircularProgressIndicator() }
                is RecommendationUiState.Success -> {
                    val recipes = (uiState as RecommendationUiState.Success).recipes
                    if (recipes.isEmpty()) {
                        Box(Modifier.fillMaxSize().padding(padding), Alignment.Center) { Text("Brak rekomendacji.") }
                    } else {
                        val pagerState = rememberPagerState(pageCount = { recipes.size })
                        Column(Modifier.padding(padding).fillMaxSize()) {
                            HorizontalPager(
                                state = pagerState,
                                modifier = Modifier.weight(1f),
                                contentPadding = PaddingValues(horizontal = 32.dp),
                                pageSpacing = 16.dp
                            ) { page -> RecipeCard(recipes[page], viewModel) }

                            Surface(tonalElevation = 8.dp) {
                                Button(
                                    onClick = {
                                        val currentRecipe = recipes[pagerState.currentPage]
                                        Log.d("RecVM", "Wybrano przepis: ${currentRecipe.name}")
                                        viewModel.selectRecipe(currentRecipe)
                                        viewModel.startImageGenerationForRecipe(currentRecipe)
                                    },
                                    modifier = Modifier.fillMaxWidth().padding(16.dp).height(56.dp)
                                ) {
                                    Text("Wybierz ten przepis")
                                }
                            }
                        }
                    }
                }
                is RecommendationUiState.Error -> {
                    Box(Modifier.fillMaxSize().padding(padding), Alignment.Center) {
                        Text("Błąd: ${(uiState as RecommendationUiState.Error).message}")
                    }
                }
                else -> {}
            }
        }
    }
}

@Composable
fun RecipeCard(recipe: RecipeRecommendation, viewModel: RecommendationViewModel) {
    var expanded by remember { mutableStateOf(false) }
    
    // Optymalizacja: zapamiętujemy sformatowany tekst, aby uniknąć ponownego parsowania JSON przy każdym odświeżeniu
    val formattedIngredients = remember(recipe.ingredients) { formatListText(recipe.ingredients) }
    val formattedInstructions = remember(recipe.instructions) { formatListText(recipe.instructions.toCleanString()) }

    Card(
        shape = RoundedCornerShape(24.dp),
        modifier = Modifier
            .fillMaxHeight(0.9f)
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(Modifier.verticalScroll(rememberScrollState())) {
            Text(
                recipe.name,
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(16.dp),
                fontWeight = FontWeight.Bold
            )

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(250.dp)
                    .background(Color(0xFFF5F5F5))
            ) {
                if (recipe.isImageLoading) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                            Spacer(Modifier.height(8.dp))
                            Text("AI generuje obraz...", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                } else {
                    val context = LocalContext.current
                    val imageRequest = remember(recipe.imageUrl) {
                        ImageRequest.Builder(context)
                            .data(recipe.imageUrl)
                            .crossfade(true)
                            .build()
                    }

                    // Przywrócono SubcomposeAsyncImage, ponieważ używamy bloków Composable w parametrze 'error'
                    coil.compose.SubcomposeAsyncImage(
                        model = imageRequest,
                        contentDescription = null,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop,
                        error = {
                            val isAi = recipe.id < 0
                            if (isAi) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .background(Color(0xFFEEEEEE)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Image(
                                        painter = painterResource(id = R.drawable.gemini_logo),
                                        contentDescription = null,
                                        modifier = Modifier.size(150.dp),
                                        contentScale = ContentScale.Fit
                                    )
                                }
                            } else {
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .background(Color(0xFFE0E0E0)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Menu,
                                        contentDescription = null,
                                        modifier = Modifier.size(48.dp),
                                        tint = Color.DarkGray
                                    )
                                }
                            }
                        }
                    )
                }
            }

            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("⏱ Czas: ${recipe.totalTime ?: "?"} min", style = MaterialTheme.typography.titleMedium)
            }

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp)
                    .clickable { expanded = !expanded }
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Szczegóły", fontWeight = FontWeight.Bold)
                    Icon(
                        imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = null
                    )
                }
                AnimatedVisibility(visible = expanded) {
                    Column {
                        Text("Składniki:", fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
                        Text(formattedIngredients, modifier = Modifier.padding(start = 8.dp))

                        Text("Instrukcje:", fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 16.dp))
                        Text(formattedInstructions, modifier = Modifier.padding(start = 8.dp))
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
fun CookingModeScreen(
    recipe: RecipeRecommendation,
    viewModel: RecommendationViewModel,
    onBack: () -> Unit,
    onFinish: (Long, Int, String) -> Unit
) {
    var showRating by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Box(modifier = Modifier.fillMaxWidth().height(300.dp).background(Color(0xFFEEEEEE))) {
            val isAi = recipe.id < 0
            val isPlaceholder = recipe.imageUrl == null
            val shouldShowSpinner = recipe.isImageLoading || (isAi && isPlaceholder)

            if (shouldShowSpinner) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.height(12.dp))
                        Text("AI generuje zdjęcie potrawy...", style = MaterialTheme.typography.bodyMedium)
                    }
                }
            } else {
                coil.compose.SubcomposeAsyncImage(
                    model = recipe.imageUrl,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop,
                    error = {
                        Icon(Icons.Default.Menu, null, Modifier.size(64.dp).align(Alignment.Center), tint = Color.Gray)
                    }
                )
            }

            IconButton(onClick = onBack, Modifier.padding(16.dp).background(Color.White.copy(alpha = 0.7f), CircleShape)) {
                Icon(Icons.Default.Close, null)
            }
        }

        Column(Modifier.padding(16.dp)) {
            Text(recipe.name, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("Składniki", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 16.dp))
            Text(formatListText(recipe.ingredients), modifier = Modifier.padding(top = 8.dp))
            Text("Instrukcje", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 16.dp))
            Text(formatListText(recipe.instructions.toCleanString()), modifier = Modifier.padding(top = 8.dp))
            Spacer(Modifier.height(32.dp))
            Button(onClick = { showRating = true }, modifier = Modifier.fillMaxWidth().height(56.dp)) {
                Text("Zakończ robienie posiłku")
            }
        }
    }

    if (showRating) {
        RatingDialog(
            onDismiss = { showRating = false },
            onConfirm = { rating, note -> onFinish(recipe.id, rating, note) }
        )
    }
}

@Composable
fun RatingDialog(onDismiss: () -> Unit, onConfirm: (Int, String) -> Unit) {
    var rating by remember { mutableStateOf(0) }
    var note by remember { mutableStateOf("") }

    Dialog(onDismissRequest = onDismiss) {
        Card(shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(24.dp).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("Jak oceniasz to danie?", style = MaterialTheme.typography.titleLarge)
                Row(Modifier.padding(vertical = 16.dp)) {
                    (1..5).forEach { index ->
                        Icon(
                            imageVector = Icons.Default.Star,
                            contentDescription = null,
                            modifier = Modifier.size(40.dp).clickable { rating = index },
                            tint = if (index <= rating) Color(0xFFFFD700) else Color.LightGray
                        )
                    }
                }

                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text("Co Ci się podobało, a co nie? (opcjonalnie)") },
                    placeholder = { Text("np. Danie smaczne, ale nie lubię kolendry...") },
                    modifier = Modifier.fillMaxWidth().height(100.dp),
                    maxLines = 3
                )

                Spacer(modifier = Modifier.height(16.dp))

                Button(onClick = { onConfirm(rating, note) }, enabled = rating > 0, modifier = Modifier.fillMaxWidth()) {
                    Text("Zatwierdź")
                }
            }
        }
    }
}
