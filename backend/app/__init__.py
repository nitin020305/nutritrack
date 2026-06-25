from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
import os

db      = SQLAlchemy()
migrate = Migrate()
jwt     = JWTManager()
mail    = Mail()

def create_app(config_name="default"):
    app = Flask(__name__, static_folder=None)

    # Load config
    from config import config
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Blueprints
    from app.routes.auth    import auth_bp
    from app.routes.user    import user_bp
    from app.routes.food    import food_bp
    from app.routes.analytics import analytics_bp
    from app.routes.admin   import admin_bp

    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(user_bp,      url_prefix="/api/user")
    app.register_blueprint(food_bp,      url_prefix="/api/food")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(admin_bp,     url_prefix="/api/admin")

    # Serve frontend
    frontend_dir = os.path.join(app.root_path, "..", "..", "frontend")

    @app.route("/")
    def index():
        return send_from_directory(os.path.join(frontend_dir, "templates"), "index.html")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(os.path.join(frontend_dir, "static"), filename)

    return app
