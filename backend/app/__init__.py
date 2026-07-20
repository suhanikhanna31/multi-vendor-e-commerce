from datetime import datetime

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

    @app.cli.command("seed-demo-data")
    def seed_demo_data():
        """Populate the DB with sample vendors, orders, and vendor/analyst
        logins so the dashboards have something to show. Safe to run
        repeatedly — skips if vendors already exist.
        """
        import random
        from datetime import timedelta

        from werkzeug.security import generate_password_hash

        from app.extensions import db
        from app.models import Order, User, UserRole, Vendor

        if Vendor.query.first():
            print("Vendors already exist — skipping demo data seed.")
            return

        vendor_names = ["Northwind Traders", "Aarohi Textiles", "Blue Ridge Goods"]
        vendors = []
        for name in vendor_names:
            v = Vendor(name=name, slug=name.lower().replace(" ", "-"), is_active=True)
            db.session.add(v)
            vendors.append(v)
        db.session.flush()  # assigns vendor.id without a full commit

        statuses = ["pending", "paid", "shipped", "failed"]
        for i in range(30):
            vendor = random.choice(vendors)
            order = Order(
                vendor_id=vendor.id,
                external_order_id=f"DEMO-{1000 + i}",
                amount_inr=round(random.uniform(500, 15000), 2),
                status=random.choice(statuses),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )
            db.session.add(order)

        vendor_user = User(
            email="vendor@example.com",
            password_hash=generate_password_hash("VendorDemo123"),
            role=UserRole.VENDOR,
            vendor_id=vendors[0].id,
        )
        analyst_user = User(
            email="analyst@example.com",
            password_hash=generate_password_hash("AnalystDemo123"),
            role=UserRole.ANALYST,
        )
        db.session.add_all([vendor_user, analyst_user])
        db.session.commit()
        print(f"Seeded {len(vendors)} vendors, 30 orders, and vendor/analyst logins.")


def _register_blueprints(app: Flask) -> None:
    from app.auth.routes import auth_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.analyst.routes import analyst_bp
    from app.blueprints.ml.routes import ml_bp
    from app.blueprints.vendor.routes import vendor_bp
    from app.webhooks.routes import webhooks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(analyst_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(webhooks_bp)
