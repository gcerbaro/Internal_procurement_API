from flask import request, jsonify
from config import VPN_PREFIX
import os

def check_vpn():
    if request.method == "OPTIONS":
        return None  # nunca bloquear preflight

    # resto da lógica VPN
    if not request.remote_addr.startswith(VPN_PREFIX):
        return jsonify({"error": "Acesso negado — requer conexão VPN ativa"}), 403

    return None
