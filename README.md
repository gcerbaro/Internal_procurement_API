# E-commerce API — Guia de Desenvolvimento

## Estrutura do Projeto

```
ecommerce_api/
│
├── app.py                  # Ponto de entrada — cria app, registra rotas e middlewares
├── config.py               # Leitura centralizada de variáveis de ambiente (.env)
├── .env.example            # Modelo de variáveis (copie para .env e ajuste)
│
├── auth/
│   ├── __init__.py
│   └── tokens.py           # Geração e decodificação de JWT
│
├── db/
│   ├── __init__.py
│   └── connection.py       # Conexão SQLite, init_db(), seed_users()
│
├── middleware/
│   ├── __init__.py
│   ├── auth_middleware.py  # Decorators @require_jwt e @require_role
│   └── vpn_middleware.py   # before_request: bloqueia IPs fora da VPN
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py      # POST /auth/login
│   ├── product_routes.py   # GET/POST /products, PUT /products/<id>
│   └── sale_routes.py      # POST /sales
│
└── utils/
    ├── __init__.py
    └── sanitize.py         # Helpers anti-SQL Injection (validação + whitelist)
```

## Instalação

```bash
pip install flask flask-openapi3 flask-limiter pyjwt bcrypt python-dotenv
cp .env.example .env   # edite JWT_SECRET e as senhas antes de subir
python app.py
```

## Problemas Resolvidos

### Problema 1 — Autenticação no Swagger UI

`SecurityScheme(type="http", scheme="bearer")` é passado ao construtor do `OpenAPI` em `app.py`.
Cada rota protegida recebe `security=[{"BearerAuth": []}]`.

**Fluxo no Swagger:**
1. Abra `http://<VPN_IP>:<PORT>/docs`
2. Faça **POST /auth/login** com username/password
3. Copie o `token` retornado
4. Clique em **Authorize 🔒** (topo da página) → cole o token → Authorize
5. Todas as rotas protegidas passam a enviar `Authorization: <token>` automaticamente

---

### Problema 2 — Refatoração Monolítica

| Camada | Arquivo | Responsabilidade |
|--------|---------|-----------------|
| Configuração | `config.py` | Único ponto de leitura do `.env` |
| Banco de dados | `db/connection.py` | Conexão, schema, seed |
| Autenticação | `auth/tokens.py` | Geração/decodificação JWT |
| Middleware | `middleware/auth_middleware.py` | `@require_jwt`, `@require_role` |
| Middleware | `middleware/vpn_middleware.py` | Filtro de IP da VPN |
| Rotas | `routes/auth_routes.py` | Login |
| Rotas | `routes/product_routes.py` | CRUD de produtos |
| Rotas | `routes/sale_routes.py` | Registro de vendas |
| Utilitários | `utils/sanitize.py` | Validação / anti-SQLi |

---

### Problema 3 — Proteção contra SQL Injection

**Camadas de defesa (defense-in-depth):**

#### Camada 1 — Parâmetros Posicionais (principal)
O driver `sqlite3` do Python usa *prepared statements* com `?`.  
Valores de usuário **nunca** são interpolados na string SQL.

```python
# ✅ CORRETO — valor nunca toca a string SQL
c.execute("SELECT * FROM users WHERE username = ?", (username,))

# ❌ ERRADO — vulnerável a SQLi
c.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

#### Camada 2 — Validação de Tipos (`utils/sanitize.py`)
Antes de qualquer query, os dados passam por:

- `sanitize_str(value, field)` — strip + limite de comprimento
- `sanitize_positive_int(value, field)` — garante int > 0
- `sanitize_positive_float(value, field)` — garante float > 0

Rejeita na origem qualquer payload que não seja do tipo esperado.

#### Camada 3 — Blocklist de Metacaracteres
`validate_no_sql_metacharacters(value, field)` rejeita strings com padrões como  
`--`, `;`, `UNION SELECT`, `DROP TABLE`, `EXEC(`, etc.

#### Camada 4 — Whitelist para ORDER BY
Parâmetros posicionais não funcionam em cláusulas `ORDER BY`.  
`safe_order_column(column, direction)` valida contra uma `frozenset` de colunas  
e direções permitidas — nunca usa a string do usuário diretamente.
