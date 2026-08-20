from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel, Field
from models import Users
from database import SessionLocal
from typing import Annotated
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt


router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/login')


SECRET_KEY = 'e79bbdebc8511bcefdaec6ce16826f54045c7d45478dad9b9111d62f9b77ffd9'
AGORITHM  = 'HS256'

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class CreateUsers(BaseModel):
    username : str
    email : str
    password: str


def authenticate_user(username, password, db):
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password, user.hash_password):
        return user
    return False

def create_access_token(username: str, user_id: int, expires_delta : timedelta):
    encode = {'sub':username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=AGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[AGORITHM])
        username : str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='User not found')
        return {'username': username, 'id': user_id}
    except:
        raise HTTPException(status_code=404, detail='User not found')

@router.post('/createuser')
def create_users(db : db_dependency, new_user : CreateUsers):
    user_model = Users(
        username = new_user.username,
        email = new_user.email,
        hash_password = bcrypt_context.hash(new_user.password)
    )
    db.add(user_model)
    db.commit()

    return JSONResponse(status_code= 201, content={'message' : 'create User Successfully'})

@router.post('/auth/login')
def login_user(db: db_dependency, form_data : Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "Failed authentication"

    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer'}