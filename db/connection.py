import os
import sqlite3
import bcrypt
from config import DB_PATH


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL,
            stock       INTEGER NOT NULL,
            created     TEXT NOT NULL,
            updated     TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            buyer      TEXT NOT NULL,
            created    TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def seed_users() -> None:
    defaults = [
        ("admin", os.getenv("ADMIN_PASSWORD", "Admin@2026!"), "admin"),
        ("prof",  os.getenv("PROF_PASSWORD",  "Prof@2026!"),  "admin"),
        ("user",  os.getenv("USER_PASSWORD",  "User@2026!"),  "user"),
    ]
    conn = get_db()
    c = conn.cursor()
    for username, plain_password, role in defaults:
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not c.fetchone():
            hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
            c.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed.decode(), role),
            )
    conn.commit()
    conn.close()
