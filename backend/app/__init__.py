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

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


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
