# app.py
from app_factory import create_app
from config import VPN_IP, PORT
from db import init_db, seed_users

app = create_app()

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
