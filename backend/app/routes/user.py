from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.auth_helpers import verified_required
from app import db
from app.models.user import User
from app.models.food_log import FoodLog
from app.services.prediction import get_full_prediction, get_calorie_target, calculate_bmr, calculate_tdee
from datetime import date, timedelta

user_bp = Blueprint("user", __name__)
#-------------__GETS CURRENT USER__----------------------------------------------------------------------------------
def _current_user():
    return User.query.get_or_404(int(get_jwt_identity()))
""""
1.get_jwt_identity() reads the user Id stored inside the jwt token
2. get_or_404 fetches the user from database or if not found returns 404 error from app.models.user
Working : returns the currently logged-in user object, or 404 if invalid.
"""
#------------------------------------__END__----------------------------------------------------

#-----__COMPLETE PROFILE(after signup)__------------------------------------------------------------
@user_bp.route("/profile", methods=["PUT"])
@verified_required  #decorator from utils — blocks unverified users
def complete_profile():
    """Fill in health details after account creation."""
    user = _current_user()
    data = request.get_json() or {}

    required = ["age", "gender", "height_cm", "weight_kg", "goal"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"Missing field: {f}"}), 400

    user.age            = int(data["age"])
    user.gender         = data["gender"].lower()
    user.height_cm      = float(data["height_cm"])
    user.weight_kg      = float(data["weight_kg"])
    user.activity_level = data.get("activity_level", "moderate")
    user.goal           = data["goal"].lower()
    user.target_weight_kg = data.get("target_weight_kg")
    user.target_days      = data.get("target_days")
    user.profile_complete = True
    db.session.commit()

    bmr  = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender) #app.services.prediction(calculate_bmr)
    tdee = calculate_tdee(bmr, user.activity_level) ##app.services.prediction(calculate_tdee)
    return jsonify({
        "message": "Profile saved",
        "user":  user.to_dict(),
        "stats": {
            "bmr":            round(bmr, 1),
            "tdee":           round(tdee, 1),
            "calorie_target": round(get_calorie_target(tdee, user.goal), 1),
        }
    })
"""
1.PUT /profile route (requires verified login) → takes health details from request body
2.Validates required fields, saves them onto the user object, commits to DB
3.Calculates BMR/TDEE/calorie target and returns them
"""
#--------------------------------__END__-----------------------------------------------------------

#-----__GET PROFILE__---------------------------------------------------------------------------------
@user_bp.route("/profile", methods=["GET"])
@verified_required #decorator from utils — blocks unverified users
def get_profile():
    user = _current_user()
    stats = {}
    if user.profile_complete:
        bmr  = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
        tdee = calculate_tdee(bmr, user.activity_level)
        stats = {
            "bmr":            round(bmr, 1),
            "tdee":           round(tdee, 1),
            "calorie_target": round(get_calorie_target(tdee, user.goal), 1),
        }
    return jsonify({"user": user.to_dict(), "stats": stats})
"""
1.GET /profile route (requires verified login) → fetches logged-in user
2.If their profile is already filled in, calculates BMR/TDEE/calorie target;
3.Returns user info + stats (empty stats if profile incomplete).
"""
#--------------------------------__END__------------------------------------------------------------


#-----__UPDATE PROFILE__------------------------------------------------------------------------------
@user_bp.route("/profile/update", methods=["PUT"])
@verified_required
def update_profile():
    user = _current_user()
    data = request.get_json() or {}
    fields = ["name","age","gender","height_cm","weight_kg",
              "activity_level","goal","target_weight_kg","target_days"]
    
    for f in fields:
        if f in data:
            setattr(user, f, data[f])
    db.session.commit()

    bmr  = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee = calculate_tdee(bmr, user.activity_level)
    return jsonify({
        "message": "Profile updated",
        "user":  user.to_dict(),
        "stats": {
            "bmr":            round(bmr, 1),
            "tdee":           round(tdee, 1),
            "calorie_target": round(get_calorie_target(tdee, user.goal), 1),
        }
    })
""""
this updated the only fields that user have sent using setattr and then recalculate bmr and tdee and calorie target
"""
#--------------------------------__END__------------------------------------------------------------


#------__PREDICTION__----------------------------------------------------------------------------------
@user_bp.route("/prediction", methods=["GET"])
@verified_required
def get_prediction():
    user = _current_user()
    since = date.today() - timedelta(days=7)
    logs  = FoodLog.query.filter(
        FoodLog.user_id == user.id, FoodLog.log_date >= since
    ).all()

    if not logs:
        bmr          = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
        tdee         = calculate_tdee(bmr, user.activity_level)
        avg_calories = get_calorie_target(tdee, user.goal)
    else:
        daily = {}
        for log in logs:
            k = log.log_date.isoformat()
            daily[k] = daily.get(k, 0) + log.calories
        avg_calories = sum(daily.values()) / len(daily)

    return jsonify(get_full_prediction(user, avg_calories))

"""
GET /prediction route (requires verified login) → looks at the user's food logs from the last 7 days,
averages their daily calorie intake (or falls back to their calorie target if no logs exist),
then passes that average into a prediction function
"""
#--------------------------------__END__------------------------------------------------------------

