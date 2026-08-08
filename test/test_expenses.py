import pytest
from datetime import date
from fastapi import status
from test_main import client
from main import app
from router.auth import get_current_user
from database import sessionLocal
from models import Transactions, Users


# 1. User Overrides Function
def override_current_user():
    return {"id": 1, "username": "testuser"}


app.dependency_overrides[get_current_user] = override_current_user


# 2. Fixture Use
@pytest.fixture  
def test_transactions():
    db = sessionLocal()
    user = db.query(Users).filter(Users.id == 1).first()
    if not user:
        user = Users(
            id=1,
            username="testuser",
            email="testuser@example.com",
        )
        db.add(user)
        db.commit()

    # Transaction Create
    transaction = Transactions(
        id=99,
        title="Salary",
        amount=50000,
        type="income",
        category="Salary",
        date=date.today(),
        owner_id=1,
    )
    db.add(transaction)
    db.commit()
    yield transaction
    db.query(Transactions).filter(Transactions.id == 99).delete()
    db.commit()
    db.close()


# 3. Test Functions
def test_get_transactions(test_transactions):
    res = client.get("/transactions")
    assert res.status_code == status.HTTP_200_OK


def test_get_specific_transactions(test_transactions):
    res = client.get("/transactions/99")
    assert res.status_code == status.HTTP_200_OK


def test_update_transactions(test_transactions):
    request_data = {
        "title": "Updated Salary",
        "amount": 60000,
        "type": "income",
        "category": "Salary",
        "date": "2026-08-08",
    }
    res = client.put("/transactions/99", json=request_data)

    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {
        "message": "Transaction updated successfully",
        "updated_fields": {
            "title": "Updated Salary",
            "amount": 60000.0,
            "type": "income",
            "category": "Salary",
            "date": "2026-08-08",
        },
    }


def test_delete(test_transactions):
    res = client.delete("/transactions/99")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"message": "Transaction deleted successfully"}
 