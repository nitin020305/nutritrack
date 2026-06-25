"""
Seed script — creates a default admin and demo user.
Run from backend/: python ../database/seed.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app, db
from app.models.user import User

app = create_app("development")

with app.app_context():
    db.create_all()

    # Admin
    if not User.query.filter_by(email="admin@nutritrack.com").first():
        admin = User(email="admin@nutritrack.com", name="Admin", role="admin", is_verified=True, is_active=True)
        admin.set_password("admin123")
        db.session.add(admin)
        print("✓ Admin created: admin@nutritrack.com / admin123")

    # Demo user
    if not User.query.filter_by(email="demo@nutritrack.com").first():
        demo = User(
            email="demo@nutritrack.com", name="Demo User",
            role="user", is_verified=True, is_active=True,
            age=28, gender="male", height_cm=175, weight_kg=72,
            activity_level="moderate", goal="lose",
            target_weight_kg=65, target_days=90,
            profile_complete=True,
        )
        demo.set_password("demo123")
        db.session.add(demo)
        print("✓ Demo user created: demo@nutritrack.com / demo123")

    db.session.commit()
    print("Seeding complete.")
