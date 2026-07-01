import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db as _db
from app.models import User, UserRole, Vendor


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def vendor(app):
    v = Vendor(name="Test Vendor", slug="test-vendor")
    _db.session.add(v)
    _db.session.commit()
    return v


@pytest.fixture
def admin_user(app):
    user = User(
        email="admin@example.com",
        password_hash=generate_password_hash("password123"),
        role=UserRole.ADMIN,
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def vendor_user(app, vendor):
    user = User(
        email="vendor@example.com",
        password_hash=generate_password_hash("password123"),
        role=UserRole.VENDOR,
        vendor_id=vendor.id,
    )
    _db.session.add(user)
    _db.session.commit()
    return user
