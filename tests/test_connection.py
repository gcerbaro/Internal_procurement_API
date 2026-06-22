import os
import tempfile
import pytest
import sqlite3

@pytest.fixture(autouse=True)
def setup_temp_db():
    """Fixture que configura um banco de dados temporário para cada teste"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    os.environ["DB_PATH"] = temp_db_path
    
    yield
    
    # Limpeza após o teste
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)
    
    # Remove da variável de ambiente
    if "DB_PATH" in os.environ:
        del os.environ["DB_PATH"]

from db.connection import get_db, init_db, seed_users


class TestGetDb:
    def test_retorna_conexao_sqlite(self):
        conn = get_db()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_row_factory_configurado(self):
        conn = get_db()
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_foreign_keys_habilitado(self):
        conn = get_db()
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
        conn.close()

    def test_wal_mode_habilitado(self):
        conn = get_db()
        result = conn.execute("PRAGMA journal_mode").fetchone()
        # Banco em arquivo deve usar WAL
        assert result[0].upper() == "WAL"
        conn.close()


class TestInitDb:
    def test_cria_tabelas(self):
        init_db()
        conn = get_db()
        
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        
        assert "users" in tables
        assert "products" in tables
        assert "sales" in tables

    def test_idempotente(self):
        """Chamar init_db duas vezes não levanta erro."""
        init_db()
        init_db()  # Segunda chamada não deve causar erro


class TestSeedUsers:
    def test_cria_usuarios_padrao(self):
        init_db()  # Primeiro cria as tabelas
        seed_users()
        conn = get_db()
        rows = conn.execute("SELECT username, role FROM users").fetchall()
        conn.close()
        
        usernames = {r["username"] for r in rows}
        assert {"admin", "prof", "user"}.issubset(usernames)

    def test_senhas_hasheadas(self):
        init_db()
        seed_users()
        conn = get_db()
        row = conn.execute("SELECT password FROM users WHERE username='admin'").fetchone()
        conn.close()
        
        # Bcrypt hashes começam com $2b$ ou $2a$
        assert row["password"].startswith("$2b") or row["password"].startswith("$2a")

    def test_idempotente_nao_duplica_usuarios(self):
        init_db()
        seed_users()
        seed_users()  
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) as n FROM users WHERE username='admin'"
        ).fetchone()["n"]
        conn.close()
        assert count == 1

    def test_roles_corretas(self):
        init_db()
        seed_users()
        conn = get_db()
        rows = {r["username"]: r["role"] for r in conn.execute(
            "SELECT username, role FROM users"
        ).fetchall()}
        conn.close()
        
        assert rows["admin"] == "admin"
        assert rows["prof"] == "admin"
        assert rows["user"] == "user"
