import bcrypt
from flask import jsonify
from flask_openapi3 import Tag
from pydantic import BaseModel, Field
from auth.tokens import generate_token
from db import get_db

auth_tag = Tag(name="auth", description="Autenticação")
class LoginBody(BaseModel):
    username: str = Field(..., example="usuario")
    password: str = Field(..., example="senha")

def register_auth_routes(app, limiter) -> None:
    @app.post(
        "/auth/login",
        tags=[auth_tag],
        summary="Autenticar usuário",
        description=(
            "Retorna um JWT válido por 2 horas. Requer VPN ativa.\n\n"
            "Copie o valor de `token` e clique em **Authorize** (topo da página) "
            "para autenticar as demais rotas."
        ),
    )
    @limiter.limit("5 per minute")
    def login(body: LoginBody):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT password, role FROM users WHERE username = ?",
            (body.username,),
        )
        row = c.fetchone()
        conn.close()

        #anti-enumeração
        if not row or not bcrypt.checkpw(
            body.password.encode(), row["password"].encode()
        ):
            return jsonify({"error": "Credenciais inválidas"}), 401

        token = generate_token(body.username, row["role"])
        return jsonify({"token": token, "expires_in": "2h"})
