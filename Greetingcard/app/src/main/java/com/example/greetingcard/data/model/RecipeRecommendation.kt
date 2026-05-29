package com.example.greetingcard.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.Transient
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive

@Serializable
data class RecipeRecommendation(
    val id: Long,
    val name: String,

    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("prep_time") val prepTime: Int? = null,
    @SerialName("cook_time") val cookTime: Int? = null,
    @SerialName("total_time") val totalTime: Int? = null,

    // --- ZMIANA: JsonElement pozwala przyjąć strukturę JSON z bazy danych jako obiekt i jako tekst ---
    val ingredients: JsonElement? = null,
    @SerialName("ingredient_names") val ingredientNames: JsonElement? = null,
    val instructions: JsonElement? = null,
    val tags: JsonElement? = null,
    val embedding: String? = null,
    val cuisine: String? = null,
    val warmth: Boolean? = null,

    val similarity: Float = 0.0f,
    @Transient var adjustedScore: Float = 0.0f,
    @Transient var isImageLoading: Boolean = false
)

fun JsonElement?.toCleanString(): String {
    if (this == null) return ""
    return try {
        when (this) {
            is JsonArray -> this.joinToString(", ") { 
                try { it.jsonPrimitive.content } catch (e: Exception) { it.toString() } 
            }
            is JsonPrimitive -> this.content
            else -> this.toString()
        }
    } catch (e: Exception) {
        ""
    }
}
