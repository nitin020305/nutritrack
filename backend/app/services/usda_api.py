"""
USDA FoodData Central API integration.
Docs: https://api.nal.usda.gov/fdc/v1/

Free, no key required for basic use (DEMO_KEY = 1000 requests/hour).
Get your own free key at: https://fdc.nal.usda.gov/api-key-signup.html
"""

import requests
from flask import current_app
from app import db
from app.models.nutrient import NutrientCache

# USDA nutrient ID → our field mapping
NUTRIENT_ID_MAP = {
    1008: "calories",        # Energy (kcal)
    1003: "protein",         # Protein
    1005: "carbs",           # Carbohydrate by difference
    1004: "fat",             # Total lipid (fat)
    1079: "fiber",           # Fiber, total dietary
    2000: "sugar",           # Sugars, total
    1093: "sodium",          # Sodium
    1092: "potassium",       # Potassium
    1087: "calcium",         # Calcium
    1089: "iron",            # Iron
    1162: "vitamin_c",       # Vitamin C
}

# Fallback nutrient data for common Indian foods (per 100g)
# Used when USDA API doesn't return good results
INDIAN_FOOD_FALLBACK = {
    "roti": {"calories": 297, "protein": 7.9, "carbs": 55.5, "fat": 3.7, "fiber": 2.9, "sugar": 0.5, "sodium": 2, "potassium": 100, "calcium": 14, "iron": 2.1, "vitamin_c": 0},
    "chapati": {"calories": 297, "protein": 7.9, "carbs": 55.5, "fat": 3.7, "fiber": 2.9, "sugar": 0.5, "sodium": 2, "potassium": 100, "calcium": 14, "iron": 2.1, "vitamin_c": 0},
    "paratha": {"calories": 326, "protein": 7.3, "carbs": 51.0, "fat": 10.3, "fiber": 2.4, "sugar": 0.4, "sodium": 3, "potassium": 95, "calcium": 13, "iron": 1.9, "vitamin_c": 0},
    "dal": {"calories": 116, "protein": 7.6, "carbs": 20.6, "fat": 0.4, "fiber": 3.8, "sugar": 1.0, "sodium": 7, "potassium": 340, "calcium": 30, "iron": 2.4, "vitamin_c": 1.2},
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28.2, "fat": 0.3, "fiber": 0.4, "sugar": 0.1, "sodium": 1, "potassium": 35, "calcium": 10, "iron": 0.2, "vitamin_c": 0},
    "ladyfinger": {"calories": 33, "protein": 1.9, "carbs": 7.5, "fat": 0.2, "fiber": 3.2, "sugar": 1.5, "sodium": 8, "potassium": 303, "calcium": 82, "iron": 0.8, "vitamin_c": 23},
    "bhindi": {"calories": 33, "protein": 1.9, "carbs": 7.5, "fat": 0.2, "fiber": 3.2, "sugar": 1.5, "sodium": 8, "potassium": 303, "calcium": 82, "iron": 0.8, "vitamin_c": 23},
    "paneer": {"calories": 265, "protein": 18.3, "carbs": 3.4, "fat": 20.8, "fiber": 0, "sugar": 3.4, "sodium": 10, "potassium": 44, "calcium": 208, "iron": 0.2, "vitamin_c": 0},
    "idli": {"calories": 58, "protein": 2.0, "carbs": 11.4, "fat": 0.2, "fiber": 0.5, "sugar": 0.2, "sodium": 190, "potassium": 55, "calcium": 20, "iron": 0.5, "vitamin_c": 0},
    "samosa": {"calories": 262, "protein": 5.8, "carbs": 32.2, "fat": 12.5, "fiber": 2.5, "sugar": 1.5, "sodium": 380, "potassium": 200, "calcium": 30, "iron": 1.5, "vitamin_c": 5},
    "poha": {"calories": 130, "protein": 2.5, "carbs": 28.5, "fat": 0.5, "fiber": 0.8, "sugar": 0.5, "sodium": 5, "potassium": 70, "calcium": 12, "iron": 0.8, "vitamin_c": 0},
    "upma": {"calories": 113, "protein": 3.1, "carbs": 19.3, "fat": 2.8, "fiber": 1.2, "sugar": 0.8, "sodium": 200, "potassium": 100, "calcium": 15, "iron": 1.0, "vitamin_c": 2},
    "khichdi": {"calories": 120, "protein": 4.5, "carbs": 22.0, "fat": 1.5, "fiber": 1.8, "sugar": 0.5, "sodium": 180, "potassium": 150, "calcium": 25, "iron": 1.2, "vitamin_c": 0},
    "curd": {"calories": 61, "protein": 3.5, "carbs": 4.7, "fat": 3.3, "fiber": 0, "sugar": 4.7, "sodium": 46, "potassium": 141, "calcium": 121, "iron": 0.1, "vitamin_c": 0.5},
    "milk": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0, "sugar": 4.8, "sodium": 44, "potassium": 150, "calcium": 113, "iron": 0.1, "vitamin_c": 0},
}

def _extract_nutrient_value(nutrient_id: int, nutrients_list: list) -> float:
    """Extract a specific nutrient value from USDA nutrient list."""
    for n in nutrients_list:
        if n.get("nutrientId") == nutrient_id or n.get("nutrient", {}).get("id") == nutrient_id:
            return float(n.get("value", n.get("amount", 0)) or 0)
    return 0.0

def _search_usda(food_name: str) -> dict | None:
    """Search USDA FoodData Central for a food item. Returns per-100g nutrients."""
    api_key = current_app.config.get("USDA_API_KEY", "DEMO_KEY")
    base_url = current_app.config.get("USDA_BASE_URL", "https://api.nal.usda.gov/fdc/v1")

    try:
        search_url = f"{base_url}/foods/search"
        params = {
            "query": food_name,
            "api_key": api_key,
            "pageSize": 5,
            "dataType": "Foundation,SR Legacy,Branded",
        }
        resp = requests.get(search_url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        foods = data.get("foods", [])
        if not foods:
            return None

        # Pick the best match (first Foundation/SR Legacy result)
        best = None
        for food in foods:
            dtype = food.get("dataType", "")
            if dtype in ("Foundation", "SR Legacy"):
                best = food
                break
        if not best:
            best = foods[0]

        nutrients_list = best.get("foodNutrients", [])
        result = {}
        for nid, field in NUTRIENT_ID_MAP.items():
            result[field] = _extract_nutrient_value(nid, nutrients_list)

        return result

    except Exception as e:
        current_app.logger.warning(f"USDA API error for '{food_name}': {e}")
        return None

def get_nutrients_per_100g(food_name: str) -> dict:
    """
    Get nutrient data (per 100g) for a food item.
    Checks DB cache first, then Indian fallback, then USDA API.

    Returns dict with keys: calories, protein, carbs, fat, fiber,
    sugar, sodium, potassium, calcium, iron, vitamin_c
    """
    food_key = food_name.lower().strip()

    # 1. Check DB cache
    cached = NutrientCache.query.filter_by(food_name=food_key).first()
    if cached:
        return {
            "calories": cached.calories_per_100g,
            "protein": cached.protein_per_100g,
            "carbs": cached.carbs_per_100g,
            "fat": cached.fat_per_100g,
            "fiber": cached.fiber_per_100g,
            "sugar": cached.sugar_per_100g,
            "sodium": cached.sodium_per_100g,
            "potassium": cached.potassium_per_100g,
            "calcium": cached.calcium_per_100g,
            "iron": cached.iron_per_100g,
            "vitamin_c": cached.vitamin_c_per_100g,
        }

    # 2. Check Indian food fallback table
    if food_key in INDIAN_FOOD_FALLBACK:
        nutrients = INDIAN_FOOD_FALLBACK[food_key]
        _save_to_cache(food_key, nutrients)
        return nutrients

    # 3. Call USDA API
    nutrients = _search_usda(food_name)

    if not nutrients:
        # Default fallback: assume generic vegetable ~35 kcal/100g
        nutrients = {
            "calories": 35, "protein": 1.5, "carbs": 6.0, "fat": 0.3,
            "fiber": 1.5, "sugar": 2.0, "sodium": 10, "potassium": 200,
            "calcium": 30, "iron": 0.5, "vitamin_c": 10,
        }

    _save_to_cache(food_key, nutrients)
    return nutrients

def _save_to_cache(food_name: str, nutrients: dict):
    """Save nutrient data to DB cache."""
    try:
        cache_entry = NutrientCache(
            food_name=food_name,
            calories_per_100g=nutrients.get("calories", 0),
            protein_per_100g=nutrients.get("protein", 0),
            carbs_per_100g=nutrients.get("carbs", 0),
            fat_per_100g=nutrients.get("fat", 0),
            fiber_per_100g=nutrients.get("fiber", 0),
            sugar_per_100g=nutrients.get("sugar", 0),
            sodium_per_100g=nutrients.get("sodium", 0),
            potassium_per_100g=nutrients.get("potassium", 0),
            calcium_per_100g=nutrients.get("calcium", 0),
            iron_per_100g=nutrients.get("iron", 0),
            vitamin_c_per_100g=nutrients.get("vitamin_c", 0),
        )
        db.session.add(cache_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()

def calculate_nutrients_for_items(parsed_items: list) -> tuple[dict, list]:
    """
    Calculate total nutrients for a list of parsed food items.

    Args:
        parsed_items: [{name, quantity, unit, grams}, ...]

    Returns:
        (total_nutrients_dict, enriched_items_list)
    """
    from app.utils.unit_converter import to_grams

    totals = {k: 0.0 for k in ["calories", "protein", "carbs", "fat",
                                 "fiber", "sugar", "sodium", "potassium",
                                 "calcium", "iron", "vitamin_c"]}
    enriched = []

    for item in parsed_items:
        grams = to_grams(item["name"], item["quantity"], item["unit"])
        nutrients_per_100g = get_nutrients_per_100g(item["name"])

        item_nutrients = {}
        for key, val in nutrients_per_100g.items():
            item_nutrients[key] = round(val * grams / 100, 2)
            totals[key] += item_nutrients[key]

        enriched.append({
            **item,
            "grams": round(grams, 1),
            "nutrients": item_nutrients,
        })

    return totals, enriched
