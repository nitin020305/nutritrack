"""
Mail service — email verification and password reset.
In development (MAIL_SUPPRESS_SEND=True) prints to console instead.
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail
from itsdangerous import URLSafeTimedSerializer
import secrets

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

# ── Token generation ──────────────────────────────────────────────────────────
def generate_verification_token(email: str) -> str:
    return _serializer().dumps(email, salt="email-verify")

def verify_email_token(token: str, max_age_hours: int = None) -> str | None:
    hours = max_age_hours or current_app.config.get("EMAIL_TOKEN_EXPIRY_HOURS", 24)
    try:
        email = _serializer().loads(token, salt="email-verify", max_age=hours * 3600)
        return email
    except Exception:
        return None

def generate_reset_token(email: str) -> str:
    return _serializer().dumps(email, salt="password-reset")

def verify_reset_token(token: str, max_age_hours: int = None) -> str | None:
    hours = max_age_hours or current_app.config.get("RESET_TOKEN_EXPIRY_HOURS", 1)
    try:
        email = _serializer().loads(token, salt="password-reset", max_age=hours * 3600)
        return email
    except Exception:
        return None

# ── Email templates ───────────────────────────────────────────────────────────
VERIFY_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family:Inter,sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px">
<div style="max-width:480px;margin:auto;background:#161d2f;border-radius:16px;padding:36px;border:1px solid #1e2d45">
  <div style="font-family:monospace;font-size:22px;color:#00d4b4;margin-bottom:16px">NutriTrack</div>
  <h2 style="margin:0 0 8px">Verify your email</h2>
  <p style="color:#64748b;margin:0 0 24px">Hi {{ name }}, click below to verify your account.</p>
  <a href="{{ url }}"
     style="display:inline-block;background:#00d4b4;color:#0a0f1e;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700">
    Verify Email →
  </a>
  <p style="color:#64748b;font-size:12px;margin-top:20px">Link expires in 24 hours.</p>
</div>
</body>
</html>
"""

RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family:Inter,sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px">
<div style="max-width:480px;margin:auto;background:#161d2f;border-radius:16px;padding:36px;border:1px solid #1e2d45">
  <div style="font-family:monospace;font-size:22px;color:#00d4b4;margin-bottom:16px">NutriTrack</div>
  <h2 style="margin:0 0 8px">Reset your password</h2>
  <p style="color:#64748b;margin:0 0 24px">Hi {{ name }}, click below to reset your password.</p>
  <a href="{{ url }}"
     style="display:inline-block;background:#f43f5e;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700">
    Reset Password →
  </a>
  <p style="color:#64748b;font-size:12px;margin-top:20px">Link expires in 1 hour. If you didn't request this, ignore this email.</p>
</div>
</body>
</html>
"""

WELCOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family:Inter,sans-serif;background:#0a0f1e;color:#e2e8f0;padding:40px">
<div style="max-width:480px;margin:auto;background:#161d2f;border-radius:16px;padding:36px;border:1px solid #1e2d45">
  <div style="font-family:monospace;font-size:22px;color:#00d4b4;margin-bottom:16px">NutriTrack</div>
  <h2 style="margin:0 0 8px">Welcome aboard, {{ name }}! 🎉</h2>
  <p style="color:#64748b;margin:0 0 24px">Your account is verified. Start tracking your nutrition today.</p>
  <a href="{{ url }}"
     style="display:inline-block;background:#00d4b4;color:#0a0f1e;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700">
    Go to Dashboard →
  </a>
</div>
</body>
</html>
"""

def _render(template: str, **kwargs) -> str:
    return render_template_string(template, **kwargs)

def _send(subject: str, recipient: str, html: str):
    msg = Message(subject=subject, recipients=[recipient], html=html)
    try:
        mail.send(msg)
        current_app.logger.info(f"Email sent: {subject} → {recipient}")
    except Exception as e:
        current_app.logger.warning(f"Email send failed (suppressed in dev): {e}")

# ── Public API ────────────────────────────────────────────────────────────────
def send_verification_email(user):
    token = generate_verification_token(user.email)
    url   = f"{current_app.config['FRONTEND_URL']}/api/auth/verify-email/{token}"
    html  = _render(VERIFY_TEMPLATE, name=user.name or "there", url=url)
    _send("Verify your NutriTrack account", user.email, html)
    return token

def send_reset_email(user):
    token = generate_reset_token(user.email)
    url   = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
    html  = _render(RESET_TEMPLATE, name=user.name or "there", url=url)
    _send("Reset your NutriTrack password", user.email, html)
    return token

def send_welcome_email(user):
    html = _render(WELCOME_TEMPLATE,
                   name=user.name or "there",
                   url=current_app.config["FRONTEND_URL"])
    _send("Welcome to NutriTrack!", user.email, html)
