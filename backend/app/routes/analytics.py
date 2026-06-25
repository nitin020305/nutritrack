from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.auth_helpers import verified_required
from app.models.food_log import FoodLog
from app.models.user import User
from app.services.prediction import get_full_prediction, get_calorie_target, calculate_bmr, calculate_tdee
from app.utils.chart_generator import (
    generate_goal_vs_actual_chart, generate_weekly_trend_chart, generate_macros_pie_chart,
)
from datetime import date, timedelta
from collections import defaultdict

analytics_bp = Blueprint("analytics", __name__)

def _uid():
    return int(get_jwt_identity())

def _aggregate_logs(logs):
    t = {k: 0.0 for k in ["calories","protein_g","carbs_g","fat_g",
                            "fiber_g","sugar_g","sodium_mg","potassium_mg",
                            "calcium_mg","iron_mg","vitamin_c_mg"]}
    for l in logs:
        t["calories"]     += l.calories
        t["protein_g"]    += l.protein_g
        t["carbs_g"]      += l.carbs_g
        t["fat_g"]        += l.fat_g
        t["fiber_g"]      += l.fiber_g
        t["sugar_g"]      += l.sugar_g
        t["sodium_mg"]    += l.sodium_mg
        t["potassium_mg"] += l.potassium_mg
        t["calcium_mg"]   += l.calcium_mg
        t["iron_mg"]      += l.iron_mg
        t["vitamin_c_mg"] += l.vitamin_c_mg
    return {k: round(v, 1) for k, v in t.items()}

def _get_goals(user):
    bmr        = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee       = calculate_tdee(bmr, user.activity_level)
    cal_target = get_calorie_target(tdee, user.goal)
    return {
        "calories":   round(cal_target, 1),
        "protein_g":  round((cal_target * 0.30) / 4, 1),
        "carbs_g":    round((cal_target * 0.45) / 4, 1),
        "fat_g":      round((cal_target * 0.25) / 9, 1),
        "fiber_g":    30.0,
        "sugar_g":    50.0,
        "sodium_mg":  2300.0,
    }

@analytics_bp.route("/daily", methods=["GET"])
@verified_required
def daily_analytics():
    uid      = _uid()
    user     = User.query.get_or_404(uid)
    log_date_str = request.args.get("date", date.today().isoformat())
    try:
        log_date = date.fromisoformat(log_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    logs   = FoodLog.query.filter_by(user_id=uid, log_date=log_date).all()
    actual = _aggregate_logs(logs)
    goals  = _get_goals(user)

    bmr          = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee         = calculate_tdee(bmr, user.activity_level)
    avg_calories = actual["calories"] if actual["calories"] > 0 else get_calorie_target(tdee, user.goal)
    prediction   = get_full_prediction(user, avg_calories)

    chart_bar = generate_goal_vs_actual_chart(goals, actual, f"Nutrients — {log_date_str}")
    chart_pie = generate_macros_pie_chart(actual["calories"], actual["protein_g"], actual["carbs_g"], actual["fat_g"])

    return jsonify({
        "date": log_date_str, "actual": actual, "goals": goals,
        "achievement_pct": {
            k: round((actual.get(k,0)/goals[k]*100),1) if goals.get(k,0) > 0 else 0
            for k in goals
        },
        "prediction": prediction,
        "meals":   [l.to_dict() for l in logs],
        "charts":  {
            "goal_vs_actual":  f"data:image/png;base64,{chart_bar}",
            "macro_breakdown": f"data:image/png;base64,{chart_pie}",
        },
    })

@analytics_bp.route("/weekly", methods=["GET"])
@verified_required
def weekly_analytics():
    uid        = _uid()
    user       = User.query.get_or_404(uid)
    end_date   = date.today()
    start_date = end_date - timedelta(days=6)

    logs = FoodLog.query.filter(
        FoodLog.user_id == uid,
        FoodLog.log_date >= start_date,
        FoodLog.log_date <= end_date,
    ).order_by(FoodLog.log_date).all()

    daily_map = defaultdict(list)
    for log in logs:
        daily_map[log.log_date.isoformat()].append(log)

    daily_summaries = []
    for i in range(7):
        day      = (start_date + timedelta(days=i)).isoformat()
        day_logs = daily_map.get(day, [])
        daily_summaries.append({"date": day, **_aggregate_logs(day_logs)})

    goals      = _get_goals(user)
    week_total = _aggregate_logs(logs)
    week_avg   = {k: round(v/7, 1) for k, v in week_total.items()}

    trend_data = [{"date": d["date"], "calories": d["calories"]} for d in daily_summaries]
    chart_trend = generate_weekly_trend_chart(trend_data, goals["calories"])
    chart_bar   = generate_goal_vs_actual_chart(
        {k: v*7 for k, v in goals.items()}, week_total, "Weekly Nutrients — Goal vs Actual"
    )
    return jsonify({
        "period":          {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "daily_summaries": daily_summaries,
        "week_total":      week_total,
        "week_average":    week_avg,
        "weekly_goals":    {k: round(v*7,1) for k, v in goals.items()},
        "charts": {
            "calorie_trend":  f"data:image/png;base64,{chart_trend}",
            "goal_vs_actual": f"data:image/png;base64,{chart_bar}",
        },
    })

@analytics_bp.route("/monthly", methods=["GET"])
@verified_required
def monthly_analytics():
    uid        = _uid()
    user       = User.query.get_or_404(uid)
    end_date   = date.today()
    start_date = end_date - timedelta(days=29)

    logs = FoodLog.query.filter(
        FoodLog.user_id == uid,
        FoodLog.log_date >= start_date,
        FoodLog.log_date <= end_date,
    ).all()

    goals       = _get_goals(user)
    month_total = _aggregate_logs(logs)
    logged_days = len(set(l.log_date for l in logs))
    month_avg   = {k: round(v/max(logged_days,1),1) for k, v in month_total.items()}

    weekly = defaultdict(list)
    for log in logs:
        week_num = log.log_date.isocalendar()[1]
        weekly[f"Week {week_num}"].append(log)

    weekly_breakdown = [
        {"week": wk, **_aggregate_logs(wl)} for wk, wl in sorted(weekly.items())
    ]
    chart_bar = generate_goal_vs_actual_chart(
        {k: v*30 for k, v in goals.items()}, month_total, "Monthly Nutrients — Goal vs Actual"
    )
    return jsonify({
        "period":                {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "month_total":           month_total,
        "month_average_per_day": month_avg,
        "monthly_goals":         {k: round(v*30,1) for k, v in goals.items()},
        "logged_days":           logged_days,
        "weekly_breakdown":      weekly_breakdown,
        "charts":                {"goal_vs_actual": f"data:image/png;base64,{chart_bar}"},
    })
