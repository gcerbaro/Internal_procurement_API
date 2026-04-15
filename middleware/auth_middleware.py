from functools import wraps
import jwt
from flask import request, jsonify
from auth.tokens import decode_token


def require_jwt(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token JWT obrigatório no formato Bearer"}), 401

        token = auth_header.split(" ")[1]

        try:
            data = decode_token(token)
            request.current_user = data["user"]
            request.current_role = data["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado! faça login novamente"}), 401
        except Exception as e:
            print("JWT ERROR:", e) 
            return jsonify({"error": "Token inválido"}), 401

        return f(*args, **kwargs)

    return wrapper


def require_role(roles: list[str]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.current_role not in roles:
                return jsonify({"error": "Forbidden, permissão insuficiente"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
