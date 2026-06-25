"""
Authorization helpers — decorators for role-based access control.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def admin_required(fn):
    """Decorator: JWT required + role must be 'admin'."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        uid  = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403
        return fn(*args, **kwargs)
    return wrapper

def verified_required(fn):
    """Decorator: JWT required + email must be verified."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        uid  = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if not user.is_verified:
            return jsonify({"error": "Please verify your email first", "code": "EMAIL_NOT_VERIFIED"}), 403
        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403
        return fn(*args, **kwargs)
    return wrapper

def active_required(fn):
    """Decorator: JWT required + account must be active (but not necessarily verified)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        uid  = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user or not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403
        return fn(*args, **kwargs)
    return wrapper
