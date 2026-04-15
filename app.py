from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_openapi3 import OpenAPI, Info, SecurityScheme
from flask import jsonify

from config import VPN_IP, PORT
from db import init_db, seed_users
from middleware.vpn_middleware import check_vpn
from routes import (
    register_auth_routes,
    register_product_routes,
    register_sale_routes,
)

_security_schemes = {
    "BearerAuth": SecurityScheme(
        type="http",
        scheme="bearer",
        bearerFormat="JWT",
        description=(
            "Cole aqui o token obtido em **POST /auth/login**.\n\n"
            "O Swagger enviará automaticamente o header `Authorization: <token>` "
            "em todas as requisições protegidas."
        ),
    )
}

info = Info(
    title="Internal Procurement API",
    version="2.0.0",
    description=(
        "API protegida por túnel VPN OpenVPN CloudConnexa.\n\n"
        "**Como autenticar no Swagger:**\n"
        "1. Faça **POST /auth/login** com suas credenciais.\n"
        "2. Copie o valor do campo `token` na resposta.\n"
        "3. Clique em **Authorize** (topo desta página) e cole o token.\n"
        "4. Todas as rotas protegidas passarão a funcionar automaticamente.\n\n"
        "**Acesso restrito:** todas as rotas de negócio exigem conexão ativa à VPN."
    ),
)

app = OpenAPI(
    __name__,
    info=info,
    doc_prefix="/docs",
    security_schemes=_security_schemes,
)
# Rate limiter global
limiter = Limiter(get_remote_address, app=app, default_limits=["50 per minute"])

# Middleware global VPN check antes de qualquer rota
app.before_request(check_vpn)

# Registro de rotas
register_auth_routes(app, limiter)
register_product_routes(app, limiter)
register_sale_routes(app, limiter)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Muitas requisições", "detail": str(e)}), 429


@app.errorhandler(422)
def validation_error(e):
    return jsonify({"error": "Dados inválidos na requisição", "detail": str(e)}), 422


if __name__ == "__main__":
    init_db()
    seed_users()

    pad = lambda s: s.ljust(42)
    swagger_url = f"http://{VPN_IP}:{PORT}/docs"

    print(f"""
╔══════════════════════════════════════════════════════╗
║           E-commerce API — em execução               ║
╠══════════════════════════════════════════════════════╣
║  Bind IP  : {pad(VPN_IP)}║
║  Porta    : {pad(str(PORT))}║
║  Swagger  : {pad(swagger_url)}║
╚══════════════════════════════════════════════════════╝
    """)
    app.run(host=VPN_IP, port=PORT, debug=False)
