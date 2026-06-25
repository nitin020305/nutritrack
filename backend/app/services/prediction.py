"""
Weight prediction engine using TDEE (Total Daily Energy Expenditure) model.

Formulas used:
  BMR  → Mifflin-St Jeor equation
  TDEE → BMR × activity multiplier
  Weight change → calorie deficit/surplus ÷ 7700 (kcal per kg of fat)
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,       # Little/no exercise
    "light": 1.375,         # Light exercise 1-3 days/week
    "moderate": 1.55,       # Moderate exercise 3-5 days/week
    "active": 1.725,        # Heavy exercise 6-7 days/week
    "very_active": 1.9,     # Very heavy exercise, physical job
}

KCAL_PER_KG_FAT = 7700     # ~3500 kcal per pound of fat

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """
    Mifflin-St Jeor BMR formula.
    Returns kcal/day the body needs at complete rest.
    """
    if gender.lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure = BMR × activity multiplier."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)
    return bmr * multiplier

def get_calorie_target(tdee: float, goal: str) -> float:
    """
    Recommended daily calorie intake based on goal.
      lose    → TDEE - 500 kcal/day (≈0.5 kg/week loss)
      gain    → TDEE + 300 kcal/day (lean bulk)
      maintain → TDEE
    """
    if goal == "lose":
        return max(tdee - 500, 1200)   # Never go below 1200
    elif goal == "gain":
        return tdee + 300
    else:
        return tdee

def predict_weight(
    current_weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
    goal: str,
    avg_daily_calories_consumed: float,
    days: int = 1,
) -> float:
    """
    Predict weight after `days` days based on calorie intake vs TDEE.

    Args:
        current_weight_kg: user's current weight
        avg_daily_calories_consumed: average calories eaten per day
        days: number of days to project forward

    Returns:
        Predicted weight in kg
    """
    bmr = calculate_bmr(current_weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)

    # Daily calorie surplus (+) or deficit (-)
    daily_delta = avg_daily_calories_consumed - tdee

    # Total calorie surplus/deficit over the period
    total_delta = daily_delta * days

    # Weight change: 7700 kcal = 1 kg of fat
    weight_change_kg = total_delta / KCAL_PER_KG_FAT

    return round(current_weight_kg + weight_change_kg, 2)

def get_full_prediction(user, avg_daily_calories: float) -> dict:
    """
    Generate weight predictions for today, +7 days, +30 days.

    Args:
        user: User model instance
        avg_daily_calories: average calories consumed per day (from food logs)

    Returns:
        dict with predictions and TDEE stats
    """
    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee = calculate_tdee(bmr, user.activity_level)
    calorie_target = get_calorie_target(tdee, user.goal)
    daily_delta = avg_daily_calories - tdee

    weight_today = user.weight_kg   # Starting point
    weight_7d = predict_weight(
        user.weight_kg, user.height_cm, user.age, user.gender,
        user.activity_level, user.goal, avg_daily_calories, 7
    )
    weight_30d = predict_weight(
        user.weight_kg, user.height_cm, user.age, user.gender,
        user.activity_level, user.goal, avg_daily_calories, 30
    )

    # Days to reach target weight
    days_to_target = None
    if user.target_weight_kg and daily_delta != 0:
        weight_diff = user.target_weight_kg - user.weight_kg
        kcal_needed = weight_diff * KCAL_PER_KG_FAT
        days_to_target = int(abs(kcal_needed / daily_delta)) if daily_delta != 0 else None

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "calorie_target": round(calorie_target, 1),
        "avg_daily_calories_consumed": round(avg_daily_calories, 1),
        "daily_calorie_delta": round(daily_delta, 1),
        "predicted_weight": {
            "today_kg": weight_today,
            "after_7_days_kg": weight_7d,
            "after_30_days_kg": weight_30d,
        },
        "days_to_target": days_to_target,
        "goal": user.goal,
        "target_weight_kg": user.target_weight_kg,
    }
