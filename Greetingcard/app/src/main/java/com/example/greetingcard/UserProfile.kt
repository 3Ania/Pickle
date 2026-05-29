package com.example.greetingcard

import kotlinx.serialization.Serializable

@Serializable
data class UserProfile(
    val id: String,
    val username: String,
    val excluded_ingredients: List<String>? = emptyList(),
    val disliked_ingredients: List<String>? = emptyList(),
    val liked_ingredients: List<String>? = emptyList(),
    val diets: List<String>? = emptyList()
)
