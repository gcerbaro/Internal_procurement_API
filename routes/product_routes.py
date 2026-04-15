from datetime import datetime
from flask import jsonify, request
from flask_openapi3 import Tag
from pydantic import BaseModel, Field
from db import get_db
from middleware import require_jwt, require_role
from utils import sanitize_str, sanitize_positive_int, sanitize_positive_float, validate_no_sql_metacharacters

products_tag = Tag(name="products", description="Gestão de produtos")
class ProductBody(BaseModel):
    name:        str   = Field(...,  example="Notebook")
    description: str   = Field("",  example="Intel i7, 16GB RAM")
    price:       float = Field(...,  example=3499.90)
    stock:       int   = Field(...,  example=10)


def register_product_routes(app, limiter) -> None:
    @app.get(
        "/products",
        tags=[products_tag],
        summary="Listar produtos",
        description="Retorna todos os produtos. **Requer JWT** no header Authorization.",
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @limiter.limit("20 per minute")
    def list_products():
        print("HEADERS:", request.headers)
        conn = get_db()
        # query sem parâmetros variáveis
        rows = conn.execute(
            "SELECT id, name, price, stock FROM products"
        ).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    @app.post(
        "/products",
        tags=[products_tag],
        summary="Criar produto",
        description=(
            "Apenas **admin** e **professor** podem criar produtos. "
            "**Requer JWT** no header Authorization."
        ),
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @require_role(["admin"])
    def create_product(body: ProductBody):
        # validação e sanitização antes de qualquer query
        name        = sanitize_str(body.name, "name")
        description = sanitize_str(body.description or "", "description") if body.description else ""
        price       = sanitize_positive_float(body.price, "price")
        stock       = sanitize_positive_int(body.stock, "stock")

        # Rejeita metacaracteres SQL em campos de texto livre
        validate_no_sql_metacharacters(name, "name")
        if description:
            validate_no_sql_metacharacters(description, "description")

        now = datetime.now().isoformat()
        conn = get_db()
        conn.execute(
            "INSERT INTO products (name, description, price, stock, created, updated) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, stock, now, now),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Produto criado com sucesso"}), 201

    @app.put(
        "/products/<int:id>",
        tags=[products_tag],
        summary="Atualizar produto",
        description=(
            "Apenas **admin** pode atualizar produtos. "
            "**Requer JWT** no header Authorization."
        ),
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @require_role(["admin"])
    def update_product(path_id: int, body: ProductBody):
        # validação e sanitização
        name        = sanitize_str(body.name, "name")
        description = sanitize_str(body.description or "", "description") if body.description else ""
        price       = sanitize_positive_float(body.price, "price")
        stock       = sanitize_positive_int(body.stock, "stock")

        validate_no_sql_metacharacters(name, "name")
        if description:
            validate_no_sql_metacharacters(description, "description")

        now = datetime.now().isoformat()
        conn = get_db()
        if not conn.execute(
            "SELECT id FROM products WHERE id = ?", (path_id,)
        ).fetchone():
            conn.close()
            return jsonify({"error": "Produto não encontrado"}), 404

        conn.execute(
            "UPDATE products "
            "SET name = ?, description = ?, price = ?, stock = ?, updated = ? "
            "WHERE id = ?",
            (name, description, price, stock, now, path_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Produto atualizado"})
        
    @app.delete(
        "/products/<int:id>",
        tags=[products_tag],
        summary="Deletar produto",
        description="Apenas **admin** pode deletar produtos. **Requer JWT**.",
        security=[{"BearerAuth": []}],
        )
    @require_jwt
    @require_role(["admin"])
    def delete_product(path_id: int):
        conn = get_db()

        # Verifica existência
        if not conn.execute(
            "SELECT id FROM products WHERE id = ?", (path_id,)
        ).fetchone():
            conn.close()
            return jsonify({"error": "Produto não encontrado"}), 404

        conn.execute(
            "DELETE FROM products WHERE id = ?", (path_id,)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Produto deletado com sucesso"})
