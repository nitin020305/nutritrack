from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app import db
from app.models.user import User
from app.services.mail_service import (
    send_verification_email, verify_email_token,
    send_reset_email, verify_reset_token, send_welcome_email
)
from app.utils.auth_helpers import active_required
from datetime import datetime
import re

auth_bp  = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _tokens(user):
    access  = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return access, refresh

# ── REGISTER ──────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name     = (data.get("name") or "").strip()

    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "Valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(email=email, name=name, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Send verification email
    try:
        token = send_verification_email(user)
        user.verification_token   = token
        user.verification_sent_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        current_app.logger.warning(f"Verification email failed: {e}")

    access, refresh = _tokens(user)
    return jsonify({
        "message":          "Account created. Please verify your email.",
        "access_token":     access,
        "refresh_token":    refresh,
        "user":             user.to_dict(),
        "profile_complete": user.profile_complete,
        "is_verified":      user.is_verified,
    }), 201

# ── LOGIN ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "This account has been disabled. Contact support."}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    access, refresh = _tokens(user)
    return jsonify({
        "message":          "Login successful",
        "access_token":     access,
        "refresh_token":    refresh,
        "user":             user.to_dict(),
        "profile_complete": user.profile_complete,
        "is_verified":      user.is_verified,
    })

# ── VERIFY EMAIL ──────────────────────────────────────────────────────────────
@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    email = verify_email_token(token)
    if not email:
        return jsonify({"error": "Verification link is invalid or has expired"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.is_verified:
        return jsonify({"message": "Email already verified"}), 200

    user.is_verified        = True
    user.verification_token = None
    db.session.commit()

    try:
        send_welcome_email(user)
    except Exception:
        pass

    # Redirect to frontend with success
    from flask import redirect
    return redirect(f"{current_app.config['FRONTEND_URL']}?verified=1")

# ── RESEND VERIFICATION ───────────────────────────────────────────────────────
@auth_bp.route("/resend-verification", methods=["POST"])
@jwt_required()
def resend_verification():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    if user.is_verified:
        return jsonify({"message": "Email already verified"}), 200
    try:
        token = send_verification_email(user)
        user.verification_token   = token
        user.verification_sent_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500
    return jsonify({"message": "Verification email sent"})

# ── FORGOT PASSWORD ───────────────────────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    user  = User.query.filter_by(email=email).first()
    # Always return success (don't leak whether email exists)
    if user and user.is_active:
        try:
            send_reset_email(user)
        except Exception as e:
            current_app.logger.warning(f"Reset email failed: {e}")
    return jsonify({"message": "If this email exists, a reset link has been sent."})

# ── RESET PASSWORD ────────────────────────────────────────────────────────────
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data     = request.get_json() or {}
    token    = data.get("token", "")
    new_pw   = data.get("new_password", "")

    email = verify_reset_token(token)
    if not email:
        return jsonify({"error": "Reset link is invalid or has expired"}), 400
    if len(new_pw) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"message": "Password reset successfully. You can now log in."})

# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    data = request.get_json() or {}

    if not user.check_password(data.get("current_password", "")):
        return jsonify({"error": "Current password is incorrect"}), 401
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"})

# ── ME ────────────────────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    stats = {}
    if user.profile_complete:
        from app.services.prediction import calculate_bmr, calculate_tdee, get_calorie_target
        bmr  = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
        tdee = calculate_tdee(bmr, user.activity_level)
        stats = {
            "bmr":            round(bmr, 1),
            "tdee":           round(tdee, 1),
            "calorie_target": round(get_calorie_target(tdee, user.goal), 1),
        }
    return jsonify({"user": user.to_dict(), "stats": stats})

# ── REFRESH ───────────────────────────────────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    uid    = get_jwt_identity()
    access = create_access_token(identity=uid)
    return jsonify({"access_token": access})

# ── DELETE ACCOUNT ────────────────────────────────────────────────────────────
@auth_bp.route("/delete-account", methods=["DELETE"])
@jwt_required()
def delete_account():
    uid  = int(get_jwt_identity())
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account permanently deleted"})
