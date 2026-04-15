from flask import request, jsonify
from config import VPN_PREFIX

def check_vpn():
    if not request.remote_addr.startswith(VPN_PREFIX):
        return jsonify({"error": "Acesso negado — requer conexão VPN ativa"}), 403

    return None
