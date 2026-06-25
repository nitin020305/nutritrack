from app import db
from datetime import datetime, date

class FoodLog(db.Model):
    __tablename__ = "food_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    meal_type = db.Column(db.String(20), default="any")  # breakfast | lunch | dinner | snack | any
    raw_input = db.Column(db.Text, nullable=False)        # original user text

    # Parsed food items stored as JSON string
    food_items = db.Column(db.JSON, nullable=False)       # [{name, qty, unit, grams}, ...]

    # Aggregated nutrients for this log entry
    calories = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    fiber_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    sodium_mg = db.Column(db.Float, default=0)
    potassium_mg = db.Column(db.Float, default=0)
    calcium_mg = db.Column(db.Float, default=0)
    iron_mg = db.Column(db.Float, default=0)
    vitamin_c_mg = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "log_date": self.log_date.isoformat(),
            "meal_type": self.meal_type,
            "raw_input": self.raw_input,
            "food_items": self.food_items,
            "nutrients": {
                "calories": round(self.calories, 1),
                "protein_g": round(self.protein_g, 1),
                "carbs_g": round(self.carbs_g, 1),
                "fat_g": round(self.fat_g, 1),
                "fiber_g": round(self.fiber_g, 1),
                "sugar_g": round(self.sugar_g, 1),
                "sodium_mg": round(self.sodium_mg, 1),
                "potassium_mg": round(self.potassium_mg, 1),
                "calcium_mg": round(self.calcium_mg, 1),
                "iron_mg": round(self.iron_mg, 1),
                "vitamin_c_mg": round(self.vitamin_c_mg, 1),
            },
            "created_at": self.created_at.isoformat(),
        }
