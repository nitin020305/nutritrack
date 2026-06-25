import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.user     import User
from app.models.food_log import FoodLog
from app.models.nutrient import NutrientCache

app = create_app("development")

@app.shell_context_processor
def ctx():
    return {"db": db, "User": User, "FoodLog": FoodLog}

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("DB tables created.")

@app.cli.command("create-admin")
def create_admin():
    """Promote a user to admin via CLI."""
    email = input("User email: ").strip()
    user  = User.query.filter_by(email=email).first()
    if not user:
        print("User not found")
        return
    user.role = "admin"
    user.is_verified = True
    db.session.commit()
    print(f"✓ {email} is now an admin")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
