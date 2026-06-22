import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["JWT_SECRET"] = "test-secret-for-tests-only-12345"

@pytest.fixture(scope="function")
def app():
    import importlib
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DB_PATH"] = db_path

    import config as _cfg
    import db.connection as _conn
    importlib.reload(_cfg)
    importlib.reload(_conn)

    from app_factory import create_app
    application = create_app(testing=True)
    # Prevent unhandled exceptions from bubbling to pytest — let Flask return 500
    application.config["PROPAGATE_EXCEPTIONS"] = False

    with application.app_context():
        _conn.init_db()
        _conn.seed_users()
        yield application

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def admin_token(client):
    rv = client.post("/auth/login", json={"username": "admin", "password": "Admin@2026!"})
    return rv.get_json()["token"]


@pytest.fixture(scope="function")
def user_token(client):
    rv = client.post("/auth/login", json={"username": "user", "password": "User@2026!"})
    return rv.get_json()["token"]


@pytest.fixture(scope="function")
def auth_admin(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def auth_user(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def sample_product(client, auth_admin):
    client.post(
        "/products",
        json={"name": "Produto Teste", "description": "Desc", "price": 99.90, "stock": 50},
        headers=auth_admin,
    )
    rv = client.get("/products", headers=auth_admin)
    return rv.get_json()[0]
