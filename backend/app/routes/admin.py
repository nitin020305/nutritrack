"""
Admin routes — protected by admin_required decorator.
Bootstrap first admin via POST /api/admin/bootstrap with ADMIN_SECRET_KEY.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.food_log import FoodLog
from app.utils.auth_helpers import admin_required
from datetime import datetime, date, timedelta
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__)

# ── BOOTSTRAP first admin ─────────────────────────────────────────────────────
@admin_bp.route("/bootstrap", methods=["POST"])
def bootstrap_admin():
    """
    One-time endpoint to promote an existing user to admin.
    Requires ADMIN_SECRET_KEY from .env for security.

    Body: { email, admin_secret_key }
    """
    data       = request.get_json() or {}
    secret_key = data.get("admin_secret_key", "")

    if secret_key != current_app.config.get("ADMIN_SECRET_KEY"):
        return jsonify({"error": "Invalid admin secret key"}), 403

    email = (data.get("email") or "").strip().lower()
    user  = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role        = "admin"
    user.is_verified = True      # Admins are auto-verified
    db.session.commit()
    return jsonify({"message": f"{email} is now an admin", "user": user.to_dict()})

# ── DASHBOARD STATS ───────────────────────────────────────────────────────────
@admin_bp.route("/stats", methods=["GET"])
@admin_required
def dashboard_stats():
    """Overall platform statistics."""
    total_users    = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    active_users   = User.query.filter_by(is_active=True).count()
    admin_users    = User.query.filter_by(role="admin").count()
    total_logs     = FoodLog.query.count()

    # Users registered in last 7 days
    since_7d       = datetime.utcnow() - timedelta(days=7)
    new_users_7d   = User.query.filter(User.created_at >= since_7d).count()

    # Logs in last 7 days
    since_date_7d  = date.today() - timedelta(days=7)
    logs_7d        = FoodLog.query.filter(FoodLog.log_date >= since_date_7d).count()

    # Goal distribution
    goal_dist = db.session.query(User.goal, func.count(User.id))\
        .filter(User.profile_complete == True)\
        .group_by(User.goal).all()

    return jsonify({
        "users": {
            "total":    total_users,
            "verified": verified_users,
            "active":   active_users,
            "admins":   admin_users,
            "new_7d":   new_users_7d,
        },
        "food_logs": {
            "total":  total_logs,
            "last_7d": logs_7d,
        },
        "goal_distribution": {g: c for g, c in goal_dist},
    })

# ── LIST USERS ────────────────────────────────────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search   = request.args.get("search", "")
    role     = request.args.get("role", "")

    q = User.query
    if search:
        q = q.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )
    if role:
        q = q.filter_by(role=role)

    total    = q.count()
    users    = q.order_by(User.created_at.desc())\
                .offset((page-1)*per_page).limit(per_page).all()

    return jsonify({
        "users":    [u.to_dict() for u in users],
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    (total + per_page - 1) // per_page,
    })

# ── GET USER ──────────────────────────────────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    user      = User.query.get_or_404(user_id)
    log_count = FoodLog.query.filter_by(user_id=user_id).count()
    return jsonify({"user": user.to_dict(), "log_count": log_count})

# ── UPDATE USER (role, active, verified) ──────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    """Admin can change role, active status, verified status."""
    me   = User.query.get(int(get_jwt_identity()))
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if "role" in data:
        if data["role"] not in ("user", "admin"):
            return jsonify({"error": "Role must be 'user' or 'admin'"}), 400
        # Prevent self-demotion
        if user.id == me.id and data["role"] != "admin":
            return jsonify({"error": "Cannot demote yourself"}), 400
        user.role = data["role"]

    if "is_active" in data:
        if user.id == me.id and not data["is_active"]:
            return jsonify({"error": "Cannot disable your own account"}), 400
        user.is_active = bool(data["is_active"])

    if "is_verified" in data:
        user.is_verified = bool(data["is_verified"])

    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict()})

# ── DELETE USER ───────────────────────────────────────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    me   = User.query.get(int(get_jwt_identity()))
    user = User.query.get_or_404(user_id)
    if user.id == me.id:
        return jsonify({"error": "Cannot delete your own account"}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted"})

# ── FOOD LOGS (admin view all) ────────────────────────────────────────────────
@admin_bp.route("/logs", methods=["GET"])
@admin_required
def list_logs():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    user_id  = request.args.get("user_id")

    q = FoodLog.query
    if user_id:
        q = q.filter_by(user_id=int(user_id))

    total = q.count()
    logs  = q.order_by(FoodLog.created_at.desc())\
              .offset((page-1)*per_page).limit(per_page).all()

    return jsonify({
        "logs":     [l.to_dict() for l in logs],
        "total":    total,
        "page":     page,
        "per_page": per_page,
    })
