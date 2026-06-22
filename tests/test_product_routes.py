import pytest


PRODUCT_PAYLOAD = {
    "name": "Notebook",
    "description": "Intel i7, 16GB",
    "price": 3499.90,
    "stock": 10,
}


# ────────────────────────────────────────────
#  GET
# ────────────────────────────────────────────

class TestListProducts:
    def test_sem_token_retorna_401(self, client):
        rv = client.get("/products")
        assert rv.status_code == 401

    def test_admin_lista_produtos(self, client, auth_admin):
        rv = client.get("/products", headers=auth_admin)
        assert rv.status_code == 200
        assert isinstance(rv.get_json(), list)

    def test_user_lista_produtos(self, client, auth_user):
        rv = client.get("/products", headers=auth_user)
        assert rv.status_code == 200

    def test_lista_vazia_no_inicio(self, client, auth_admin):
        rv = client.get("/products", headers=auth_admin)
        assert rv.get_json() == []

    def test_lista_contem_produto_criado(self, client, auth_admin, sample_product):
        rv = client.get("/products", headers=auth_admin)
        produtos = rv.get_json()
        assert len(produtos) == 1
        assert produtos[0]["name"] == "Produto Teste"

    def test_campos_retornados(self, client, auth_admin, sample_product):
        rv = client.get("/products", headers=auth_admin)
        produto = rv.get_json()[0]
        for campo in ("id", "name", "price", "stock"):
            assert campo in produto


# ────────────────────────────────────────────
#  POST
# ────────────────────────────────────────────

class TestCreateProduct:
    def test_admin_cria_produto(self, client, auth_admin):
        rv = client.post("/products", json=PRODUCT_PAYLOAD, headers=auth_admin)
        assert rv.status_code == 201
        assert "criado" in rv.get_json()["message"]

    def test_user_nao_pode_criar(self, client, auth_user):
        rv = client.post("/products", json=PRODUCT_PAYLOAD, headers=auth_user)
        assert rv.status_code == 403

    def test_sem_token_retorna_401(self, client):
        rv = client.post("/products", json=PRODUCT_PAYLOAD)
        assert rv.status_code == 401
        
    def test_nome_vazio_causa_erro(self, client, auth_admin):
        payload = {**PRODUCT_PAYLOAD, "name": ""}
        rv = client.post("/products", json=payload, headers=auth_admin)
        assert rv.status_code in (400, 422)

    def test_preco_negativo_causa_erro(self, client, auth_admin):
        payload = {**PRODUCT_PAYLOAD, "price": -10.0}
        rv = client.post("/products", json=payload, headers=auth_admin)
        assert rv.status_code in (400, 422)

    def test_preco_zero_causa_erro(self, client, auth_admin):
        payload = {**PRODUCT_PAYLOAD, "price": 0}
        rv = client.post("/products", json=payload, headers=auth_admin)
        assert rv.status_code in (400, 422)

    def test_stock_zero_causa_erro(self, client, auth_admin):
        payload = {**PRODUCT_PAYLOAD, "stock": 0}
        rv = client.post("/products", json=payload, headers=auth_admin)
        assert rv.status_code in (400, 422)

    def test_nome_com_sql_injection_causa_erro(self, client, auth_admin):
        payload = {**PRODUCT_PAYLOAD, "name": "x'; DROP TABLE products--"}
        rv = client.post("/products", json=payload, headers=auth_admin)
        assert rv.status_code in (400, 422)
        lista = client.get("/products", headers=auth_admin).get_json()
        assert lista == []

    def test_body_faltando_campos_obrigatorios(self, client, auth_admin):
        rv = client.post("/products", json={"name": "Produto"}, headers=auth_admin)
        assert rv.status_code == 422

    def test_sem_body_retorna_422(self, client, auth_admin):
        rv = client.post("/products", headers=auth_admin)
        assert rv.status_code == 422

    def test_multiplos_produtos_criados(self, client, auth_admin):
        for i in range(3):
            client.post(
                "/products",
                json={**PRODUCT_PAYLOAD, "name": f"Produto {i}"},
                headers=auth_admin,
            )
        rv = client.get("/products", headers=auth_admin)
        assert len(rv.get_json()) == 3


# ────────────────────────────────────────────
#  PUT
# ────────────────────────────────────────────

class TestUpdateProduct:
    def test_sem_token_retorna_401(self, client, sample_product):
        pid = sample_product["id"]
        rv = client.put(f"/products/{pid}", json={"name": "X", "price": 1.0, "stock": 1})
        assert rv.status_code == 401

    def test_user_sem_role_admin_retorna_403(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        rv = client.put(
            f"/products/{pid}",
            json={"name": "X", "price": 1.0, "stock": 1},
            headers=auth_user,
        )
        assert rv.status_code == 403

    def test_admin_put(self, client, auth_admin, sample_product):
        pid = sample_product["id"]
        rv = client.put(
            f"/products/{pid}",
            json={"name": "Novo", "description": "d", "price": 10.0, "stock": 5},
            headers=auth_admin,
        )
        assert rv.status_code == 200

    def test_produto_inexistente(self, client, auth_admin):
        rv = client.put(
            "/products/9999",
            json={"name": "X", "price": 1.0, "stock": 1},
            headers=auth_admin,
        )
        assert rv.status_code==404


# ────────────────────────────────────────────
#  DELETE
# ────────────────────────────────────────────

class TestDeleteProduct:
    def test_sem_token_retorna_401(self, client, sample_product):
        pid = sample_product["id"]
        rv = client.delete(f"/products/{pid}")
        assert rv.status_code == 401

    def test_user_nao_pode_deletar(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        rv = client.delete(f"/products/{pid}", headers=auth_user)
        assert rv.status_code == 403

    def test_admin_delete(self, client, auth_admin, sample_product):
        pid = sample_product["id"]
        rv = client.delete(f"/products/{pid}", headers=auth_admin)
        assert rv.status_code==200

    def test_produto_inexistente(self, client, auth_admin):
        rv = client.delete("/products/9999", headers=auth_admin)
        assert rv.status_code==404
