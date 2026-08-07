from fastapi import FastAPI, Depends
import models
from router import auth
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine, sessionLocal

app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def Home():
    return "Hello Next Level Developer💀"
