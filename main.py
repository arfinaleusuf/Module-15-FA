from fastapi import FastAPI, Depends, HTTPException, Query
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
import models
from models import Transactions, Users
from typing import Annotated, Optional,Literal
from router import auth
from router.auth import get_current_user
from datetime import date

app = FastAPI()

class Transaction(BaseModel):
    title : str
    amount : float = Field(gt=0)
    type : Literal["income", "expense"]
    category : str
    date : date

class update_transection(BaseModel):
    title : Optional[str] = None
    amount : Optional[float] = Field(default= None, gt = 0)
    type : Literal["income", "expense"] = Optional[str]
    category: Optional[str] = None

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.post('/transactions')
def create_transactions(user : user_dependency, db: db_dependency, new_transaction: Transaction):
    if user is None:
        raise HTTPException(status_code= 401, detail='Failed Authentication')
    transaction_model = Transactions(**new_transaction.model_dump(), owner_id = user.get('id'))
    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model

@app.get('/transactions')
def get_all_transaction(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code= 401, detail='Failed Authentication')
    return db.query(Transactions).filter(Transactions.owner_id == user.get('id')).all()

@app.get('/transactions/filter')
def filter_transaction(user: user_dependency, db: db_dependency, type:Optional[str] = Query(default=None,  description="Select transaction type", example= 'income'), category: Optional[str] = Query(default= None, example='food'), minimum_amount: Optional[float] = None, maximum_amount: Optional[float] = None):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    query = db.query(Transactions).filter(Transactions.owner_id == user.get('id'))

    if type is not None:
        query = query.filter(Transactions.type == type)

    if category is not None:
        query = query.filter(Transactions.category == category)

    if minimum_amount is not None:
        query = query.filter(Transactions.amount >= minimum_amount)

    if maximum_amount is not None:
        query = query.filter(Transactions.amount <= maximum_amount)

    return query.all()

@app.get('/transactions/{transaction_id}')
def get_transaction_by_id(user: user_dependency, db : db_dependency, transaction_id : int):
    if user is None:
        raise HTTPException(status_code= 401, detail='Failed Authentication')
    specific_transcation = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if specific_transcation is not None:
        return specific_transcation
    else:
        raise HTTPException(status_code=404, detail='Transaction not Found')

@app.put('/transactions/{transaction_id}')
def update_transections(user: user_dependency, db: db_dependency, transaction_id : int, update_tran : update_transection):
    if user is None:
            raise HTTPException(status_code= 401, detail='Failed Authentication')

    tran = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if tran is None:
        raise HTTPException(status_code=404, detail='Transaction Not Found')
    update_data = update_tran.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tran, key, value)

    db.commit()

    return tran


@app.delete('/transactions/{transaction_id}')
def delete_transacrion(user : user_dependency, db : db_dependency, transaction_id : int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()

    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction Not Found')
    db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).delete()
    db.commit()
    return JSONResponse(status_code=200, content={'message':'Transaction deleted Sucessfully'})
