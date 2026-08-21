from datetime import date
from fastapi import status
from fastapi.testclient import TestClient
from main import app
from router.auth import get_current_user
from database import SessionLocal
from models import Transactions

client = TestClient(app)


def override_get_current_user():
    return {
        'id': 1,
        'username': 'testuser'
    }


app.dependency_overrides[get_current_user] = override_get_current_user


def test_transaction():
    db = SessionLocal()

    db.query(Transactions).filter(Transactions.id == 99).delete()

    test_item = Transactions(
        id=99,
        title='Lunch',
        amount=250.0,
        type='expense',
        category='Food',
        date=date(2026, 8, 22),
        owner_id=1
    )

    db.add(test_item)
    db.commit()


def test_read_all_transactions():
    response = client.get('/transactions')
    assert response.status_code == status.HTTP_200_OK

def test_read_specific_transaction():
    response = client.get('/transactions/99')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == 99
    assert data['title'] == 'Lunch'
    assert data['amount'] == 250.0
    assert data['type'] == 'expense'


def test_create_transaction():
    db = SessionLocal()

    db.query(Transactions).filter(Transactions.title == 'Monthly Salary').delete()
    db.commit()

    request_data = {
        "title": "Monthly Salary",
        "amount": 50000.0,
        "type": "income",
        "category": "Salary",
        "date": "2026-08-22"
    }

    response = client.post('/transactions', json=request_data)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
    data = response.json()
    assert data['title'] == 'Monthly Salary'
    assert data['amount'] == 50000.0
    assert data['type'] == 'income'


def test_update_transaction():

    request_data = {
        "title": "Dinner",
        "amount": 450.0,
        "type": "expense",
        "category": "Food",
        "date": "2026-08-22"
    }

    response = client.put('/transactions/99', json=request_data)
    assert response.status_code == status.HTTP_200_OK


def test_delete_transaction():

    response = client.delete('/transactions/99')
    assert response.status_code == status.HTTP_200_OK