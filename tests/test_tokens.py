import time
import pytest
import jwt as pyjwt

from auth.tokens import generate_token, decode_token


class TestGenerateToken:
    def test_retorna_string(self):
        token = generate_token("alice", "admin")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_payload_correto(self):
        token = generate_token("bob", "user")
        payload = decode_token(token)
        assert payload["user"] == "bob"
        assert payload["role"] == "user"

    def test_campos_obrigatorios_no_payload(self):
        token = generate_token("carol", "admin")
        payload = decode_token(token)
        assert "exp" in payload

    def test_tokens_diferentes_para_usuarios_diferentes(self):
        t1 = generate_token("u1", "user")
        t2 = generate_token("u2", "user")
        assert t1 != t2

    def test_tokens_diferentes_para_roles_diferentes(self):
        t1 = generate_token("alice", "admin")
        t2 = generate_token("alice", "user")
        assert t1 != t2


class TestDecodeToken:
    def test_decodifica_token_valido(self):
        token = generate_token("alice", "admin")
        data = decode_token(token)
        assert data["user"] == "alice"
        assert data["role"] == "admin"

    def test_levanta_erro_token_invalido(self):
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token("token.invalido.aqui")

    def test_levanta_erro_token_adulterado(self):
        token = generate_token("alice", "user")
        partes = token.split(".")
        # Adultera assinatura
        adulterado = partes[0] + "." + partes[1] + ".assinaturafalsa"
        with pytest.raises(pyjwt.InvalidTokenError):
            decode_token(adulterado)

    def test_levanta_erro_token_expirado(self):
        import os
        os.environ["JWT_SECRET"] = "test-secret-for-tests-only"
        # Gera token já expirado manualmente
        from datetime import datetime, timedelta, timezone
        from config import JWT_SECRET
        payload = {
            "user": "alice",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)
