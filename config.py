import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH:    str = os.getenv("DB_PATH",    "ecommerce.db")
JWT_SECRET: str = os.getenv("JWT_SECRET", "fallback-inseguro-troque-no-env")
VPN_IP:     str = os.getenv("VPN_BIND_IP","100.96.1.2")
PORT:       int = int(os.getenv("PORT",   "5000"))

# Prefixo de rede do CloudConnexa (bloco 100.64.0.0/10)
VPN_PREFIX: str = "100."
