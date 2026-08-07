from fastapi import APIRouter, HTTPException, status
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated
from database import sessionLocal
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt

router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_barear = OAuth2PasswordBearer(tokenUrl="/auth/login")
SECRET_KEY = "562de2311ff38d4b0543891bada2dfd931e8547071a0b25aa7f87c43ef1b4f43"
ALGORITHM = "HS256"


class createUsers(BaseModel):
    email: str
    username: str
    password: str


def authenticate_user(username, password, db):
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password, user.hashed_password):
        return user

    return False


def generate_access_token(username: str, user_id: str, expires: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
def get_current_user(token: Annotated[str, Depends(OAuth2_barear)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail="user not found!")
        return {"username": username, "id": user_id}
    except:
        raise HTTPException(status_code=404, detail="user not found!")


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(db: db_dependency, newUser: createUsers):
    # 1. Check if user already exists
    existing_user = (
        db.query(Users)
        .filter((Users.email == newUser.email) | (Users.username == newUser.username))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # 2. Hash password and create user
    user_model = Users(
        email=newUser.email,
        username=newUser.username,
        hashed_password=bcrypt_context.hash(newUser.password),
    )

    db.add(user_model)
    db.commit()

    return {"status": "Successful", "message": "User created successfully"}


@router.post("/auth/login")
def login(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "Failed Authentication"
    token = generate_access_token(user.username, user.id, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}
