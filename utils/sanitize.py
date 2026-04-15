import re
from typing import Any

_MAX_LENGTHS: dict[str, int] = {
    "username":    64,
    "password":   128,
    "name":       200,
    "description": 2000,
    "role":        32,
}

# Colunas permitidas em ORDER BY (whitelist explícita)
_ALLOWED_ORDER_COLUMNS: frozenset[str] = frozenset(
    {"id", "name", "price", "stock", "created", "updated"}
)

_ALLOWED_ORDER_DIRS: frozenset[str] = frozenset({"ASC", "DESC"})


def sanitize_str(value: Any, field: str = "input") -> str:
    if not isinstance(value, str):
        raise ValueError(f"Campo '{field}' deve ser uma string.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"Campo '{field}' não pode ser vazio.")
    max_len = _MAX_LENGTHS.get(field, 500)
    if len(cleaned) > max_len:
        raise ValueError(
            f"Campo '{field}' excede o comprimento máximo de {max_len} caracteres."
        )
    return cleaned


def sanitize_positive_int(value: Any, field: str = "input") -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Campo '{field}' deve ser um inteiro.")
    if value <= 0:
        raise ValueError(f"Campo '{field}' deve ser maior que zero.")
    return value


def sanitize_positive_float(value: Any, field: str = "input") -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"Campo '{field}' deve ser um número.")
    if value <= 0:
        raise ValueError(f"Campo '{field}' deve ser maior que zero.")
    return float(value)


def safe_order_column(column: str, direction: str = "ASC") -> tuple[str, str]:
    col = column.strip().lower()
    if col not in _ALLOWED_ORDER_COLUMNS:
        raise ValueError(
            f"Coluna de ordenação inválida: '{column}'. "
            f"Permitidas: {sorted(_ALLOWED_ORDER_COLUMNS)}"
        )
    dir_ = direction.strip().upper()
    if dir_ not in _ALLOWED_ORDER_DIRS:
        raise ValueError("Direção de ordenação inválida. Use ASC ou DESC.")
    return col, dir_


def validate_no_sql_metacharacters(value: str, field: str = "input") -> str:
    # Padrões que nunca deveriam aparecer em dados normais
    SUSPICIOUS = re.compile(
        r"(--|;|/\*|\*/|xp_|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO"
        r"|DELETE\s+FROM|UPDATE\s+\w+\s+SET|EXEC\s*\()",
        re.IGNORECASE,
    )
    if SUSPICIOUS.search(value):
        raise ValueError(
            f"Campo '{field}' contém sequências não permitidas."
        )
    return value
