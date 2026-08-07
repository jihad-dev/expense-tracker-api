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
    amount: float = Field(
        ..., gt=0, description="Amount must be greater than zero"
    )
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