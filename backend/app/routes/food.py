from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.auth_helpers import verified_required
from app import db
from app.models.food_log import FoodLog
from app.models.user import User
from app.services.food_parser import parse_food_input
from app.services.usda_api import calculate_nutrients_for_items
from datetime import date

food_bp = Blueprint("food", __name__)

def _uid():
    return int(get_jwt_identity())

# ── LOG FOOD ──────────────────────────────────────────────────────────────────
@food_bp.route("/log", methods=["POST"])
@verified_required
def log_food():
    uid  = _uid()
    data = request.get_json() or {}

    if not data.get("food_input"):
        return jsonify({"error": "food_input is required"}), 400

    log_date = date.today()
    if data.get("log_date"):
        try:
            log_date = date.fromisoformat(data["log_date"])
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    parsed_items = parse_food_input(data["food_input"])
    if not parsed_items:
        return jsonify({"error": "Could not parse any food items from input"}), 400

    total_nutrients, enriched_items = calculate_nutrients_for_items(parsed_items)

    food_log = FoodLog(
        user_id   = uid,
        log_date  = log_date,
        meal_type = data.get("meal_type", "any"),
        raw_input = data["food_input"],
        food_items= enriched_items,
        calories     = total_nutrients["calories"],
        protein_g    = total_nutrients["protein"],
        carbs_g      = total_nutrients["carbs"],
        fat_g        = total_nutrients["fat"],
        fiber_g      = total_nutrients["fiber"],
        sugar_g      = total_nutrients["sugar"],
        sodium_mg    = total_nutrients["sodium"],
        potassium_mg = total_nutrients["potassium"],
        calcium_mg   = total_nutrients["calcium"],
        iron_mg      = total_nutrients["iron"],
        vitamin_c_mg = total_nutrients["vitamin_c"],
    )
    db.session.add(food_log)
    db.session.commit()

    return jsonify({
        "message":         "Food logged successfully",
        "log":             food_log.to_dict(),
        "parsed_items":    enriched_items,
        "total_nutrients": {
            "calories":   round(total_nutrients["calories"], 1),
            "protein_g":  round(total_nutrients["protein"],  1),
            "carbs_g":    round(total_nutrients["carbs"],    1),
            "fat_g":      round(total_nutrients["fat"],      1),
            "fiber_g":    round(total_nutrients["fiber"],    1),
            "sugar_g":    round(total_nutrients["sugar"],    1),
            "sodium_mg":  round(total_nutrients["sodium"],   1),
        }
    }), 201

# ── GET LOGS ──────────────────────────────────────────────────────────────────
@food_bp.route("/log", methods=["GET"])
@verified_required
def get_food_logs():
    uid   = _uid()
    query = FoodLog.query.filter_by(user_id=uid)
    if request.args.get("date"):
        try:
            query = query.filter_by(log_date=date.fromisoformat(request.args["date"]))
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    logs = query.order_by(FoodLog.log_date.desc(), FoodLog.created_at.desc()).all()
    return jsonify({"logs": [l.to_dict() for l in logs], "count": len(logs)})

# ── DELETE LOG ────────────────────────────────────────────────────────────────
@food_bp.route("/log/<int:log_id>", methods=["DELETE"])
@verified_required
def delete_food_log(log_id):
    uid = _uid()
    log = FoodLog.query.get_or_404(log_id)
    if log.user_id != uid:
        return jsonify({"error": "Not authorised"}), 403
    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": f"Log {log_id} deleted"})

# ── SEARCH FOOD ───────────────────────────────────────────────────────────────
@food_bp.route("/search", methods=["GET"])
@verified_required
def search_food():
    food_name = request.args.get("q")
    if not food_name:
        return jsonify({"error": "q (food name) is required"}), 400
    qty  = float(request.args.get("qty", 1))
    unit = request.args.get("unit", "piece")
    from app.services.usda_api import get_nutrients_per_100g
    from app.utils.unit_converter import to_grams
    grams             = to_grams(food_name, qty, unit)
    nutrients_per_100g = get_nutrients_per_100g(food_name)
    result = {k: round(v * grams / 100, 2) for k, v in nutrients_per_100g.items()}
    return jsonify({
        "food": food_name, "quantity": qty, "unit": unit,
        "grams": round(grams, 1), "nutrients": result, "per_100g": nutrients_per_100g,
    })
