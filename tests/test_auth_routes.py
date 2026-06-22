import pytest


class TestLogin:
    def test_login_admin_sucesso(self, client):
        rv = client.post("/auth/login", json={"username": "admin", "password": "Admin@2026!"})
        assert rv.status_code == 200
        data = rv.get_json()
        assert "token" in data
        assert data["expires_in"] == "2h"

    def test_login_user_sucesso(self, client):
        rv = client.post("/auth/login", json={"username": "user", "password": "User@2026!"})
        assert rv.status_code == 200
        assert "token" in rv.get_json()

    def test_login_prof_sucesso(self, client):
        rv = client.post("/auth/login", json={"username": "prof", "password": "Prof@2026!"})
        assert rv.status_code == 200

    def test_senha_errada_retorna_401(self, client):
        rv = client.post("/auth/login", json={"username": "admin", "password": "senhaerrada"})
        assert rv.status_code == 401
        assert "Credenciais inválidas" in rv.get_json()["error"]

    def test_usuario_inexistente_retorna_401(self, client):
        rv = client.post("/auth/login", json={"username": "fantasma", "password": "qualquer"})
        assert rv.status_code == 401
        assert "Credenciais inválidas" in rv.get_json()["error"]

    def test_body_faltando_retorna_422(self, client):
        rv = client.post("/auth/login", json={})
        assert rv.status_code == 422

    def test_body_sem_password_retorna_422(self, client):
        rv = client.post("/auth/login", json={"username": "admin"})
        assert rv.status_code == 422

    def test_body_sem_username_retorna_422(self, client):
        rv = client.post("/auth/login", json={"password": "Admin@2026!"})
        assert rv.status_code == 422

    def test_token_gerado_e_decodificavel(self, client):
        rv = client.post("/auth/login", json={"username": "admin", "password": "Admin@2026!"})
        token = rv.get_json()["token"]
        from auth.tokens import decode_token
        payload = decode_token(token)
        assert payload["user"] == "admin"
        assert payload["role"] == "admin"

    def test_user_token_tem_role_user(self, client):
        rv = client.post("/auth/login", json={"username": "user", "password": "User@2026!"})
        token = rv.get_json()["token"]
        from auth.tokens import decode_token
        payload = decode_token(token)
        assert payload["role"] == "user"
