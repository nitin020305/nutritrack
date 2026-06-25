"""
Converts Indian and common food units to grams.
Covers: bowl, katori, roti, plate, cup, glass, piece, slice, tbsp, tsp, handful
"""

# Default grams per unit per food category
UNIT_MAP = {
    # Indian units
    "bowl": 180,
    "katori": 150,
    "plate": 300,
    "glass": 200,
    "cup": 240,
    "half cup": 120,

    # Pieces/counts — generic defaults, overridden per food below
    "piece": 100,
    "pieces": 100,
    "slice": 30,
    "slices": 30,

    # Spoon measures
    "tbsp": 15,
    "tablespoon": 15,
    "tsp": 5,
    "teaspoon": 5,

    # Handfuls
    "handful": 30,
    "fistful": 30,
}

# Food-specific overrides for piece/unit counts
FOOD_PIECE_GRAMS = {
    "roti": 35,
    "chapati": 35,
    "paratha": 60,
    "puri": 25,
    "idli": 40,
    "dosa": 80,
    "egg": 55,
    "banana": 120,
    "apple": 180,
    "orange": 150,
    "mango": 200,
    "guava": 100,
    "tomato": 90,
    "onion": 80,
    "potato": 150,
    "samosa": 60,
    "bread": 30,           # 1 slice
    "biscuit": 10,
    "cookie": 15,
    "ladoo": 35,
    "barfi": 40,
    "rasgulla": 50,
    "chicken leg": 120,
    "chicken breast": 150,
    "fish": 100,
}

def to_grams(food_name: str, quantity: float, unit: str) -> float:
    """
    Convert food quantity in a given unit to grams.

    Args:
        food_name: e.g. "roti", "banana"
        quantity: numeric amount e.g. 4, 1.5
        unit: e.g. "bowl", "piece", "roti" (bare count)

    Returns:
        float: weight in grams
    """
    food_lower = food_name.lower().strip()
    unit_lower = unit.lower().strip() if unit else "piece"

    # If unit is missing or "piece/pieces", use food-specific grams
    if unit_lower in ("", "piece", "pieces", "nos", "no", "number", "count", "unit"):
        grams_each = FOOD_PIECE_GRAMS.get(food_lower, 100)
        return quantity * grams_each

    # If the unit itself matches the food name (e.g., "4 roti" — unit = "roti")
    if unit_lower == food_lower:
        grams_each = FOOD_PIECE_GRAMS.get(food_lower, 100)
        return quantity * grams_each

    # Lookup standard unit
    grams_per_unit = UNIT_MAP.get(unit_lower)
    if grams_per_unit:
        return quantity * grams_per_unit

    # If unit is already grams/kg/ml/l
    if unit_lower in ("g", "gram", "grams"):
        return quantity
    if unit_lower in ("kg", "kilogram", "kilograms"):
        return quantity * 1000
    if unit_lower in ("ml", "milliliter", "milliliters"):
        return quantity  # 1ml ≈ 1g for liquids approximation
    if unit_lower in ("l", "liter", "liters", "litre", "litres"):
        return quantity * 1000

    # Fallback: assume piece
    grams_each = FOOD_PIECE_GRAMS.get(food_lower, 100)
    return quantity * grams_each
