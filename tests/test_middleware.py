import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
import jwt as pyjwt

from auth.tokens import generate_token
from middleware.auth_middleware import require_jwt, require_role
from middleware.vpn_middleware import check_vpn

@pytest.fixture
def jwt_app():
    """Mini-app só com as rotas de teste."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/protected")
    @require_jwt
    def protected():
        return jsonify({"user": request_user_role()})

    @app.route("/admin-only")
    @require_jwt
    @require_role(["admin"])
    def admin_only():
        return jsonify({"ok": True})

    @app.route("/multi-role")
    @require_jwt
    @require_role(["admin", "professor"])
    def multi_role():
        return jsonify({"ok": True})

    return app

def request_user_role():
    from flask import request
    return f"{request.current_user}:{request.current_role}"


@pytest.fixture
def vpn_app():
    """Mini-app para testar o check_vpn."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/rota")
    def rota():
        result = check_vpn()
        if result:
            return result
        return jsonify({"ok": True})

    return app


# ────────────────────────────────────────────
#  require_jwt
# ────────────────────────────────────────────

class TestRequireJwt:
    def test_sem_header_retorna_401(self, jwt_app):
        with jwt_app.test_client() as c:
            rv = c.get("/protected")
            assert rv.status_code == 401
            assert "JWT" in rv.get_json()["error"]

    def test_header_sem_bearer_retorna_401(self, jwt_app):
        with jwt_app.test_client() as c:
            rv = c.get("/protected", headers={"Authorization": "Basic abc"})
            assert rv.status_code == 401

    def test_token_invalido_retorna_401(self, jwt_app):
        with jwt_app.test_client() as c:
            rv = c.get("/protected", headers={"Authorization": "Bearer tokeninvalido"})
            assert rv.status_code == 401
            assert "inválido" in rv.get_json()["error"]

    def test_token_expirado_retorna_401(self, jwt_app):
        from datetime import datetime, timedelta, timezone
        from config import JWT_SECRET
        payload = {
            "user": "alice",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
        with jwt_app.test_client() as c:
            rv = c.get("/protected", headers={"Authorization": f"Bearer {expired}"})
            assert rv.status_code == 401
            assert "expirado" in rv.get_json()["error"]

    def test_token_valido_passa(self, jwt_app):
        token = generate_token("alice", "admin")
        with jwt_app.test_client() as c:
            rv = c.get("/protected", headers={"Authorization": f"Bearer {token}"})
            assert rv.status_code == 200
            assert "alice" in rv.get_json()["user"]


# ────────────────────────────────────────────
#  require_role
# ────────────────────────────────────────────

class TestRequireRole:
    def test_role_correto_passa(self, jwt_app):
        token = generate_token("alice", "admin")
        with jwt_app.test_client() as c:
            rv = c.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
            assert rv.status_code == 200

    def test_role_incorreto_retorna_403(self, jwt_app):
        token = generate_token("bob", "user")
        with jwt_app.test_client() as c:
            rv = c.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
            assert rv.status_code == 403
            assert "permissão" in rv.get_json()["error"]

    def test_multi_role_aceita_qualquer_um(self, jwt_app):
        for role in ["admin", "professor"]:
            token = generate_token("x", role)
            with jwt_app.test_client() as c:
                rv = c.get("/multi-role", headers={"Authorization": f"Bearer {token}"})
                assert rv.status_code == 200

    def test_multi_role_rejeita_desconhecido(self, jwt_app):
        token = generate_token("x", "user")
        with jwt_app.test_client() as c:
            rv = c.get("/multi-role", headers={"Authorization": f"Bearer {token}"})
            assert rv.status_code == 403


# ────────────────────────────────────────────
#  check_vpn
# ────────────────────────────────────────────

class TestCheckVpn:
    def test_ip_vpn_permitido(self, vpn_app):
        with vpn_app.test_client() as c:
            # Simula IP dentro da VPN (100.x.x.x)
            rv = c.get("/rota", environ_base={"REMOTE_ADDR": "100.64.1.50"})
            assert rv.status_code == 200

    def test_ip_fora_da_vpn_negado(self, vpn_app):
        with vpn_app.test_client() as c:
            rv = c.get("/rota", environ_base={"REMOTE_ADDR": "192.168.1.1"})
            assert rv.status_code == 403
            assert "VPN" in rv.get_json()["error"]

    def test_ip_localhost_negado(self, vpn_app):
        with vpn_app.test_client() as c:
            rv = c.get("/rota", environ_base={"REMOTE_ADDR": "127.0.0.1"})
            assert rv.status_code == 403
