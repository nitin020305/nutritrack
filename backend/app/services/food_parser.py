"""
Parses natural language food input into structured items.

Handles inputs like:
  - "ladyfinger 1 bowl with 4 roti and 1 banana"
  - "2 boiled eggs, rice 1 cup, dal 1 katori"
  - "chicken curry 1 plate + 3 roti"
  - "1 glass milk and 2 biscuits"
  - "oats 50g with 1 banana"
"""

import re
from typing import List, Dict, Optional

STOP_WORDS = {"with", "also", "some", "little", "boiled", "fried", "roasted",
              "steamed", "cooked", "raw", "fresh", "a", "an", "the", "of", "in"}

UNIT_WORDS = {
    "bowl", "bowls", "katori", "katoris", "plate", "plates", "cup", "cups",
    "glass", "glasses", "piece", "pieces", "slice", "slices",
    "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons",
    "handful", "handfuls", "fistful",
    "g", "gram", "grams", "kg", "kilogram", "kilograms",
    "ml", "milliliter", "milliliters", "l", "liter", "liters",
    "nos", "no", "number",
}

# These words act as separators between food items
ITEM_SEPARATORS = {"and", "plus", "with"}

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "half": 0.5, "quarter": 0.25,
}


def _normalize(text: str) -> str:
    """Normalize separators to a consistent delimiter."""
    # Replace commas and semicolons
    text = re.sub(r'[,;]', '|', text)
    # Replace separator words only when surrounded by spaces (not inside food names)
    text = re.sub(r'\s+\+\s+', '|', text)
    # Replace "and", "plus", "with" as separators
    text = re.sub(r'\s+(and|plus|with)\s+', '|', text, flags=re.IGNORECASE)
    return text


def _try_number(tok: str) -> Optional[float]:
    """Parse a token as a number. Returns None if not a number."""
    tok = tok.lower().strip()
    if tok in NUMBER_WORDS:
        return NUMBER_WORDS[tok]
    # Handle inline gram notation: "50g", "100ml", "200g"
    m = re.match(r'^(\d+(?:\.\d+)?)(g|kg|ml|l)$', tok)
    if m:
        return None   # handled separately
    try:
        return float(tok)
    except ValueError:
        return None


def _parse_inline_unit(tok: str):
    """Handle tokens like '50g', '200ml', '1.5kg'. Returns (qty, unit) or None."""
    m = re.match(r'^(\d+(?:\.\d+)?)(g|kg|ml|l)$', tok.lower())
    if m:
        return float(m.group(1)), m.group(2)
    return None


def _parse_chunk(chunk: str) -> Optional[Dict]:
    """
    Parse a single food chunk like:
      "ladyfinger 1 bowl" / "4 roti" / "oats 50g" / "rice 2 cups"
    Returns {name, quantity, unit, raw} or None.
    """
    chunk = chunk.strip()
    if not chunk:
        return None

    tokens = chunk.split()
    quantity = 1.0
    unit = ""
    food_tokens = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]
        tok_lower = tok.lower()

        # Check for inline unit (e.g., "50g", "200ml")
        inline = _parse_inline_unit(tok)
        if inline is not None:
            quantity, unit = inline
            i += 1
            continue

        # Try as a plain number
        num = _try_number(tok)
        if num is not None:
            quantity = num
            # Next token might be a unit word
            if i + 1 < len(tokens) and tokens[i + 1].lower() in UNIT_WORDS:
                unit = tokens[i + 1].lower()
                i += 2
                continue
            i += 1
            continue

        # Is it a unit word?
        if tok_lower in UNIT_WORDS:
            unit = tok_lower
            i += 1
            continue

        # Skip leading stop words (not if there's already food text)
        if tok_lower in STOP_WORDS and not food_tokens:
            i += 1
            continue

        food_tokens.append(tok_lower)
        i += 1

    if not food_tokens:
        return None

    food_name = " ".join(food_tokens)
    # If unit matches food name (e.g. "roti" unit), normalize
    if unit == food_name or unit in food_name.split():
        unit = "piece"
    if not unit:
        unit = "piece"

    return {
        "name": food_name,
        "quantity": quantity,
        "unit": unit,
        "raw": chunk,
    }


def parse_food_input(text: str) -> List[Dict]:
    """
    Main entry. Parse free-text food input into structured items.

    Args:
        text: e.g. "ladyfinger 1 bowl with 4 roti and 1 banana"

    Returns:
        List of [{name, quantity, unit, raw}, ...]
    """
    # First normalize separators
    normalized = _normalize(text)
    chunks = [c.strip() for c in normalized.split('|') if c.strip()]

    results = []
    for chunk in chunks:
        item = _parse_chunk(chunk)
        if item:
            results.append(item)
    return results


# ── Quick self-test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "ladyfinger 1 bowl with 4 roti and 1 banana",
        "rice 2 cups, dal 1 katori, 2 boiled eggs",
        "chicken curry 1 plate + 3 roti",
        "1 glass milk and 2 biscuits",
        "samosa 3 pieces",
        "oats 50g with 1 banana",
        "paneer 100g and dal 1 katori",
    ]
    for t in tests:
        print(f"\nInput : {t}")
        for item in parse_food_input(t):
            print(f"  → {item}")
