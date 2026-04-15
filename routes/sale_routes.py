from datetime import datetime
from flask import jsonify, request
from flask_openapi3 import Tag
from pydantic import BaseModel, Field
from db import get_db
from middleware import require_jwt, require_role
from utils import sanitize_positive_int

sales_tag = Tag(name="sales", description="Vendas")
class SaleBody(BaseModel):
    product_id: int = Field(..., example=1)
    quantity:   int = Field(..., example=2)


def register_sale_routes(app, limiter) -> None:
    @app.post(
        "/sales",
        tags=[sales_tag],
        summary="Registrar venda",
        description=(
            "Todos os roles autenticados podem realizar uma venda. "
            "**Requer JWT** no header Authorization."
        ),
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @limiter.limit("10 per minute")
    def create_sale(body: SaleBody):
        product_id = sanitize_positive_int(body.product_id, "product_id")
        quantity   = sanitize_positive_int(body.quantity,   "quantity")

        conn = get_db()
        row = conn.execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Produto não encontrado"}), 404
        if row["stock"] < quantity:
            conn.close()
            return jsonify({"error": "Estoque insuficiente"}), 400

        # parâmetros posicionais em ambas as queries
        conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (row["stock"] - quantity, product_id),
        )
        conn.execute(
            "INSERT INTO sales (product_id, quantity, buyer, created) VALUES (?, ?, ?, ?)",
            (product_id, quantity, request.current_user, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Venda registrada com sucesso"}), 201
            
    @app.delete(
        "/sales/<int:id>",
        tags=[sales_tag],
        summary="Deletar venda",
        description="Apenas **admin** pode deletar vendas. **Requer JWT**.",
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @require_role(["admin"])
    def delete_sale(path_id: int):
        conn = get_db()

        if not conn.execute(
            "SELECT id FROM sales WHERE id = ?", (path_id,)
        ).fetchone():
            conn.close()
            return jsonify({"error": "Venda não encontrada"}), 404

        conn.execute(
            "DELETE FROM sales WHERE id = ?", (path_id,)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Venda deletada com sucesso"})
        
    @app.get(
        "/sales",
        tags=[sales_tag],
        summary="Listar todas as vendas",
        description="Apenas **admin** pode visualizar todas as vendas.",
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @require_role(["admin"])
    def get_sales():
        conn = get_db()

        rows = conn.execute(
            "SELECT id, product_id, quantity, buyer, created FROM sales"
        ).fetchall()

        conn.close()
        return jsonify([dict(r) for r in rows])
        
        
    @app.get(
        "/my_purchases",
        tags=[sales_tag],
        summary="Minhas compras",
        description="Retorna as compras do usuário autenticado.",
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    def my_purchases():
        conn = get_db()

        rows = conn.execute(
            "SELECT id, product_id, quantity, buyer, created "
            "FROM sales WHERE buyer = ?",
            (request.current_user,)
        ).fetchall()

        conn.close()
        return jsonify([dict(r) for r in rows])
