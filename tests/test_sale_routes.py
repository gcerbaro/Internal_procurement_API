import pytest


class TestCreateSale:
    def test_user_realiza_venda(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": 2}, headers=auth_user)
        assert rv.status_code == 201
        assert "registrada" in rv.get_json()["message"]

    def test_admin_realiza_venda(self, client, auth_admin, sample_product):
        pid = sample_product["id"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_admin)
        assert rv.status_code == 201

    def test_sem_token_retorna_401(self, client, sample_product):
        rv = client.post("/sales", json={"product_id": sample_product["id"], "quantity": 1})
        assert rv.status_code == 401

    def test_produto_inexistente_retorna_404(self, client, auth_user):
        rv = client.post("/sales", json={"product_id": 9999, "quantity": 1}, headers=auth_user)
        assert rv.status_code == 404

    def test_estoque_insuficiente_retorna_400(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": 9999}, headers=auth_user)
        assert rv.status_code == 400
        assert "Estoque" in rv.get_json()["error"]

    def test_quantidade_zero_causa_erro(self, client, auth_user, sample_product):
        """[BUG-2] ValueError não capturado → 500."""
        pid = sample_product["id"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": 0}, headers=auth_user)
        assert rv.status_code in (400, 422, 500)

    def test_quantidade_negativa_causa_erro(self, client, auth_user, sample_product):
        """[BUG-2] ValueError não capturado → 500."""
        pid = sample_product["id"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": -1}, headers=auth_user)
        assert rv.status_code in (400, 422, 500)

    def test_venda_decrementa_estoque(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        estoque_inicial = sample_product["stock"]
        client.post("/sales", json={"product_id": pid, "quantity": 3}, headers=auth_user)
        rv = client.get("/products", headers=auth_admin)
        produto_atualizado = next(p for p in rv.get_json() if p["id"] == pid)
        assert produto_atualizado["stock"] == estoque_inicial - 3

    def test_body_faltando_retorna_422(self, client, auth_user):
        rv = client.post("/sales", json={}, headers=auth_user)
        assert rv.status_code == 422

    def test_venda_todo_estoque_disponivel(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        stock = sample_product["stock"]
        rv = client.post("/sales", json={"product_id": pid, "quantity": stock}, headers=auth_user)
        assert rv.status_code == 201

    def test_venda_apos_estoque_zerado_retorna_400(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        stock = sample_product["stock"]
        client.post("/sales", json={"product_id": pid, "quantity": stock}, headers=auth_user)
        rv = client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        assert rv.status_code == 400


class TestGetSales:
    def test_admin_lista_vendas(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv = client.get("/sales", headers=auth_admin)
        assert rv.status_code == 200
        assert len(rv.get_json()) >= 1
    
    def test_rate_limiter_lista_vendas(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv = client.get("/sales", headers=auth_admin)
        rv = client.get("/sales", headers=auth_admin)
        rv = client.get("/sales", headers=auth_admin)
        assert rv.status_code == 429

    def test_user_nao_pode_listar_todas_vendas(self, client, auth_user):
        rv = client.get("/sales", headers=auth_user)
        assert rv.status_code == 403

    def test_sem_token_retorna_401(self, client):
        rv = client.get("/sales")
        assert rv.status_code == 401

    def test_campos_retornados(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv = client.get("/sales", headers=auth_admin)
        venda = rv.get_json()[0]
        for campo in ("id", "product_id", "quantity", "buyer", "created"):
            assert campo in venda

    def test_buyer_registrado_corretamente(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv = client.get("/sales", headers=auth_admin)
        assert rv.get_json()[0]["buyer"] == "user"


class TestDeleteSale:
    def test_sem_token_retorna_401(self, client):
        rv = client.delete("/sales/1")
        assert rv.status_code == 401

    def test_user_nao_pode_deletar_venda(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv_sales = client.get("/sales", headers=auth_admin)
        sid = rv_sales.get_json()[0]["id"]
        rv = client.delete(f"/sales/{sid}", headers=auth_user)
        assert rv.status_code == 403

    def test_admin_delete_bug1(self, client, auth_admin, auth_user, sample_product):
        """[BUG-1] path_id não passado ao handler → 500."""
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        rv_sales = client.get("/sales", headers=auth_admin)
        sid = rv_sales.get_json()[0]["id"]
        rv = client.delete(f"/sales/{sid}", headers=auth_admin)
        assert rv.status_code==200

    def test_venda_inexistente_bug1(self, client, auth_admin):
        """[BUG-1] 404 fica inacessível por TypeError."""
        rv = client.delete("/sales/9999", headers=auth_admin)
        assert rv.status_code==404


class TestMyPurchases:
    def test_user_ve_proprias_compras(self, client, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 2}, headers=auth_user)
        rv = client.get("/my_purchases", headers=auth_user)
        assert rv.status_code == 200
        compras = rv.get_json()
        assert len(compras) == 1
        assert compras[0]["buyer"] == "user"

    def test_sem_token_retorna_401(self, client):
        rv = client.get("/my_purchases")
        assert rv.status_code == 401

    def test_usuario_ve_apenas_suas_compras(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_admin)
        rv = client.get("/my_purchases", headers=auth_user)
        compras = rv.get_json()
        assert all(c["buyer"] == "user" for c in compras)

    def test_sem_compras_retorna_lista_vazia(self, client, auth_user):
        rv = client.get("/my_purchases", headers=auth_user)
        assert rv.status_code == 200
        assert rv.get_json() == []

    def test_multiplas_compras_retornadas(self, client, auth_admin, auth_user, sample_product):
        pid = sample_product["id"]
        client.post("/sales", json={"product_id": pid, "quantity": 1}, headers=auth_user)
        client.post("/sales", json={"product_id": pid, "quantity": 2}, headers=auth_user)
        rv = client.get("/my_purchases", headers=auth_user)
        assert len(rv.get_json()) == 2
