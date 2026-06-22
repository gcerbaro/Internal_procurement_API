from flask import request, jsonify
from config import VPN_PREFIX
import os

def check_vpn():
    #if os.getenv("TESTING") == "1":
    #    return
    if not request.remote_addr.startswith(VPN_PREFIX):
        return jsonify({"error": "Acesso negado — requer conexão VPN ativa"}), 403

    return None
