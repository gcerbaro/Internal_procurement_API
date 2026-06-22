import pytest
from utils.sanitize import (
    sanitize_str,
    sanitize_positive_int,
    sanitize_positive_float,
    safe_order_column,
    validate_no_sql_metacharacters,
)


class TestSanitizeStr:
    def test_retorna_string_limpa(self):
        assert sanitize_str("  hello  ", "name") == "hello"

    def test_aceita_string_normal(self):
        result = sanitize_str("Notebook Pro", "name")
        assert result == "Notebook Pro"

    def test_levanta_se_nao_string(self):
        with pytest.raises(ValueError, match="deve ser uma string"):
            sanitize_str(123, "name")

    def test_levanta_se_vazio(self):
        with pytest.raises(ValueError, match="não pode ser vazio"):
            sanitize_str("   ", "name")

    def test_levanta_se_excede_comprimento(self):
        with pytest.raises(ValueError, match="comprimento máximo"):
            sanitize_str("x" * 201, "name")

    def test_comprimento_maximo_personalizado_description(self):
        # description tem max 2000
        ok = sanitize_str("a" * 2000, "description")
        assert len(ok) == 2000

    def test_levanta_description_muito_longa(self):
        with pytest.raises(ValueError):
            sanitize_str("a" * 2001, "description")

    def test_campo_desconhecido_usa_500(self):
        ok = sanitize_str("a" * 500, "campo_x")
        assert len(ok) == 500
        with pytest.raises(ValueError):
            sanitize_str("a" * 501, "campo_x")


class TestSanitizePositiveInt:
    def test_aceita_inteiro_positivo(self):
        assert sanitize_positive_int(5, "stock") == 5

    def test_levanta_se_zero(self):
        with pytest.raises(ValueError, match="maior que zero"):
            sanitize_positive_int(0, "stock")

    def test_levanta_se_negativo(self):
        with pytest.raises(ValueError):
            sanitize_positive_int(-1, "stock")

    def test_levanta_se_float(self):
        with pytest.raises(ValueError, match="deve ser um inteiro"):
            sanitize_positive_int(1.5, "stock")

    def test_levanta_se_bool(self):
        with pytest.raises(ValueError, match="deve ser um inteiro"):
            sanitize_positive_int(True, "stock")

    def test_levanta_se_string(self):
        with pytest.raises(ValueError):
            sanitize_positive_int("5", "stock")


class TestSanitizePositiveFloat:
    def test_aceita_float_positivo(self):
        assert sanitize_positive_float(9.99, "price") == 9.99

    def test_aceita_inteiro_como_float(self):
        assert sanitize_positive_float(10, "price") == 10.0

    def test_levanta_se_zero(self):
        with pytest.raises(ValueError, match="maior que zero"):
            sanitize_positive_float(0.0, "price")

    def test_levanta_se_negativo(self):
        with pytest.raises(ValueError):
            sanitize_positive_float(-5.0, "price")

    def test_levanta_se_bool(self):
        with pytest.raises(ValueError):
            sanitize_positive_float(True, "price")

    def test_levanta_se_string(self):
        with pytest.raises(ValueError):
            sanitize_positive_float("5.0", "price")


class TestSafeOrderColumn:
    def test_aceita_coluna_valida(self):
        col, dir_ = safe_order_column("price", "ASC")
        assert col == "price"
        assert dir_ == "ASC"

    def test_normaliza_para_minusculo(self):
        col, _ = safe_order_column("PRICE")
        assert col == "price"

    def test_normaliza_direcao_para_maiusculo(self):
        _, dir_ = safe_order_column("id", "asc")
        assert dir_ == "ASC"

    def test_default_direcao_asc(self):
        _, dir_ = safe_order_column("id")
        assert dir_ == "ASC"

    def test_levanta_coluna_invalida(self):
        with pytest.raises(ValueError, match="inválida"):
            safe_order_column("senha")

    def test_levanta_direcao_invalida(self):
        with pytest.raises(ValueError, match="inválida"):
            safe_order_column("id", "SIDEWAYS")

    @pytest.mark.parametrize("col", ["id", "name", "price", "stock", "created", "updated"])
    def test_todas_colunas_permitidas(self, col):
        c, _ = safe_order_column(col)
        assert c == col


class TestValidateNoSqlMetacharacters:
    def test_aceita_string_normal(self):
        result = validate_no_sql_metacharacters("Notebook Pro", "name")
        assert result == "Notebook Pro"

    @pytest.mark.parametrize("payload", [
        "--",
        ";",
        "/* comentario */",
        "UNION SELECT * FROM users",
        "DROP TABLE products",
        "INSERT INTO x",
        "DELETE FROM y",
        "UPDATE tabela SET col=1",
        "EXEC(cmd)",
        "xp_cmdshell",
    ])
    def test_rejeita_payloads_sql_injection(self, payload):
        with pytest.raises(ValueError, match="sequências não permitidas"):
            validate_no_sql_metacharacters(payload, "name")

    def test_case_insensitive(self):
        with pytest.raises(ValueError):
            validate_no_sql_metacharacters("union select 1", "name")
