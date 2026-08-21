from fastapi.testclient import TestClient
from main import app
from router.auth import get_current_user


def override_get_current_user():
    return {
        "id": 1,
        "username": "testuser"
    }


app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def test_get_transactions():
    response = client.get("/transactions")

    assert response.status_code == 200


def test_get_specific_transaction():
    response = client.get("/transactions/1")

    assert response.status_code in [200, 404]


def test_create_transaction():
    transaction_data = {
        "title": "Lunch",
        "amount": 500,
        "type": "expense",
        "category": "Food"
    }

    response = client.post(
        "/transactions",
        json=transaction_data
    )

    assert response.status_code == 201


def test_update_transaction():
    update_data = {
        "title": "Updated Lunch",
        "amount": 600
    }

    response = client.put(
        "/transactions/1",
        json=update_data
    )

    assert response.status_code in [200, 404]


def test_delete_transaction():
    response = client.delete("/transactions/1")

    assert response.status_code in [200, 404]