from datetime import datetime
from flask import jsonify, request
from flask_openapi3 import Tag
from pydantic import BaseModel, Field
from db import get_db
from middleware import require_jwt, require_role
from utils import sanitize_positive_int

sales_tag = Tag(name="sales", description="Vendas")
class SalePath(BaseModel):
    id: int = Field(..., json_schema_extra={"example": 1})
    
class SaleBody(BaseModel):
    product_id: int = Field(..., json_schema_extra={"example":1})
    quantity:   int = Field(..., json_schema_extra={"example":2})

class SaleDTO(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    buyer: str
    created: str


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
    
    @app.put(
        "/sales/<int:id>",
        tags=[sales_tag],
        summary="Atualizar venda",
        description=(
            "Apenas **admin** pode atualizar vendas. "
            "**Requer JWT** no header Authorization."
        ),
        security=[{"BearerAuth": []}],
    )
    @require_jwt
    @limiter.limit("5 per minute")
    @require_role(["admin"])
    def update_sale(path: SalePath, body: SaleBody):
        # validação e sanitização
        try:
            quantity = sanitize_str(body.quantity, "quantity")
            validate_no_sql_metacharacters(quantity, "quantity")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        now = datetime.now().isoformat()
        conn = get_db()
        if not conn.execute(
            "SELECT id FROM sales WHERE id = ?", (path.id,)
        ).fetchone():
            conn.close()
            return jsonify({"error": "Venda não encontrada"}), 404

        conn.execute(
            "UPDATE sales "
            "SET quantity = ?, updated = ? "
            "WHERE id = ?",
            (quantity, now, path.id),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Venda atualizado"})

    @app.delete(
    "/sales/<int:id>",
    tags=[sales_tag],
    summary="Deletar venda",
    description="Apenas **admin** pode deletar vendas. **Requer JWT**.",
    security=[{"BearerAuth": []}],
    )
    @require_jwt
    @limiter.limit("5 per minute")
    @require_role(["admin"])
    def delete_sale(path: SalePath):
        conn = get_db()

        if not conn.execute(
            "SELECT id FROM sales WHERE id = ?", (path.id,)
        ).fetchone():
            conn.close()
            return jsonify({"error": "Venda não encontrada"}), 404

        conn.execute(
            "DELETE FROM sales WHERE id = ?", (path.id,)
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
    @limiter.limit("2 per minute") #VALOR EXCLUSIVO PARA TESTAR NO PYTEST
    @require_role(["admin"])
    def get_sales():
        conn = get_db()

        rows = conn.execute("""
            SELECT
                s.id,
                s.product_id,
                p.name AS product_name,
                s.quantity,
                s.buyer,
                s.created
            FROM sales s
            JOIN products p
                ON p.id = s.product_id
        """).fetchall()

        sales = [
            SaleDTO(
                id=row["id"],
                product_id=row["product_id"],
                product_name=row["product_name"],
                quantity=row["quantity"],
                buyer=row["buyer"],
                created=row["created"],
            )
            for row in rows
        ]

        conn.close()
        return jsonify([dict(r) for r in sales])
        
        
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
