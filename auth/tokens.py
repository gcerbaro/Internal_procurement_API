from datetime import datetime, timedelta, timezone

import jwt

from config import JWT_SECRET

_ALGORITHM = "HS256"
_TOKEN_TTL  = timedelta(hours=2)


def generate_token(user: str, role: str) -> str:
    payload = {
        "user": user,
        "role": role,
        "exp":  datetime.now(timezone.utc) + _TOKEN_TTL,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Lança jwt.ExpiredSignatureError ou jwt.InvalidTokenError em caso de falha.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITHM])
