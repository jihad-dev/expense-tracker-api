from datetime import date
from typing import Annotated, Literal
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import engine, sessionLocal
import models
from models import Transactions
from router import auth
from router.auth import get_current_user

app = FastAPI()
app.include_router(auth.router)

# Create database tables
models.Base.metadata.create_all(bind=engine)


# Database dependency
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Pydantic schema for request validation
class TransactionCreate(BaseModel):
    title: str
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    type: Literal["income", "expense"]
    category: str
    date: date


@app.get("/")
def home():
    return "Hello Next Level Developer💀"


@app.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(
    user: user_dependency,
    db: db_dependency,
    newTransaction: TransactionCreate,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication!",
        )

    # Convert Pydantic model to dictionary and inject owner_id
    transaction_model = Transactions(
        **newTransaction.model_dump(), owner_id=user.get("id")
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Transaction created successfully",
            "transaction_id": transaction_model.id,
        },
    )


@app.get("/transactions")
def get_transactions(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Failed Authentication!")
        return (
            db.query(Transactions).filter(Transactions.owner_id == user.get("id")).all()
        )


@app.get("/transactions/{transaction_id}")
def get_specific_transaction(
    transaction_id: int, db: db_dependency, user: user_dependency
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication!",
        )
    transaction = (
        db.query(Transactions)
        .filter(Transactions.id == transaction_id)
        .filter(Transactions.owner_id == user.get("id"))
        .first()
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_transaction(user: user_dependency, db: db_dependency, transaction_id: int):
    # 1. Authentication Check
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed Authentication!",
        )

    # 2. Fetch the target transaction owned by the logged-in user
    transaction = (
        db.query(Transactions)
        .filter(Transactions.id == transaction_id)
        .filter(Transactions.owner_id == user.get("id"))
        .first()
    )

    # 3. Handle Not Found
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # 4. Delete and Commit
    db.delete(transaction)
    db.commit()

    return {"message": "Transaction deleted successfully"}
