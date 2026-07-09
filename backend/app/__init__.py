from flask import Flask

from app.config import get_config
from app.extensions import cors, db, jwt, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    _register_blueprints(app)
    _register_cli(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


def _register_cli(app: Flask) -> None:
    import os

    @app.cli.command("seed-admin")
    def seed_admin():
        """Create the admin user from ADMIN_EMAIL/ADMIN_PASSWORD env vars.

        Safe to run on every deploy — does nothing if the user already
        exists. This is how a first login gets created on hosts (e.g.
        Render's free tier) where a shell isn't available.
        """
        from werkzeug.security import generate_password_hash

        from app.extensions import db
        from app.models import User, UserRole

        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not email or not password:
            print("ADMIN_EMAIL / ADMIN_PASSWORD not set — skipping admin seed.")
            return

        if User.query.filter_by(email=email).first():
            print(f"Admin user {email} already exists — skipping.")
            return

        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.ADMIN,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user {email}.")


def _register_blueprints(app: Flask) -> None:
    from app.auth.routes import auth_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.analyst.routes import analyst_bp
    from app.blueprints.vendor.routes import vendor_bp
    from app.webhooks.routes import webhooks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(analyst_bp)
    app.register_blueprint(webhooks_bp)
