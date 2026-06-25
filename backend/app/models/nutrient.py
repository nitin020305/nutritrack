from app import db
from datetime import datetime

class NutrientCache(db.Model):
    """Cache USDA API results to avoid repeated calls for the same food."""
    __tablename__ = "nutrient_cache"

    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    usda_fdc_id = db.Column(db.Integer, nullable=True)

    # Per 100g values
    calories_per_100g = db.Column(db.Float, default=0)
    protein_per_100g = db.Column(db.Float, default=0)
    carbs_per_100g = db.Column(db.Float, default=0)
    fat_per_100g = db.Column(db.Float, default=0)
    fiber_per_100g = db.Column(db.Float, default=0)
    sugar_per_100g = db.Column(db.Float, default=0)
    sodium_per_100g = db.Column(db.Float, default=0)
    potassium_per_100g = db.Column(db.Float, default=0)
    calcium_per_100g = db.Column(db.Float, default=0)
    iron_per_100g = db.Column(db.Float, default=0)
    vitamin_c_per_100g = db.Column(db.Float, default=0)

    cached_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "food_name": self.food_name,
            "per_100g": {
                "calories": self.calories_per_100g,
                "protein_g": self.protein_per_100g,
                "carbs_g": self.carbs_per_100g,
                "fat_g": self.fat_per_100g,
                "fiber_g": self.fiber_per_100g,
                "sugar_g": self.sugar_per_100g,
                "sodium_mg": self.sodium_per_100g,
                "potassium_mg": self.potassium_per_100g,
                "calcium_mg": self.calcium_per_100g,
                "iron_mg": self.iron_per_100g,
                "vitamin_c_mg": self.vitamin_c_per_100g,
            },
        }
