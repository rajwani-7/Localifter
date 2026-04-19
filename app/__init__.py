import os
from importlib.util import find_spec

from flask import Flask

from app.extensions import bcrypt, csrf, db, login_manager


def _ensure_default_admin_credentials() -> None:
    from app.models.user import User

    admin = User.query.filter(User.role == "admin", User.email.in_(["admin", "admin@localift.com"])).first()
    if not admin:
        admin = User(full_name="Platform Admin", email="admin", role="admin", is_active=True)
        db.session.add(admin)

    admin.full_name = "Platform Admin"
    admin.email = "admin"
    admin.role = "admin"
    admin.is_active = True
    admin.set_password("admin")
    db.session.commit()


def _resolve_database_uri() -> str:
    configured_uri = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
    if configured_uri:
        # Render may provide legacy postgres:// URLs; SQLAlchemy expects postgresql://.
        if configured_uri.startswith("postgres://"):
            configured_uri = configured_uri.replace("postgres://", "postgresql://", 1)
        if configured_uri.startswith("mysql") and find_spec("pymysql") is None:
            return f"sqlite:///{os.path.join(os.getcwd(), 'localift_flask.db')}"
        return configured_uri

    # Optional explicit local MySQL URL for development machines only.
    local_mysql_uri = os.environ.get("LOCAL_MYSQL_URL")
    if local_mysql_uri and find_spec("pymysql") is not None:
        return local_mysql_uri

    # On Render, fall back to /tmp sqlite only if DATABASE_URL was not injected.
    if os.environ.get("RENDER"):
        return "sqlite:////tmp/localift_flask.db"

    return f"sqlite:///{os.path.join(os.getcwd(), 'localift_flask.db')}"


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = _resolve_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from app.models import admin_log, booking, helper, helper_application, notification, review, user
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.helper import helper_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(helper_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _ensure_default_admin_credentials()

    return app


# WSGI entrypoint for production servers (e.g., gunicorn app:app).
app = create_app()
