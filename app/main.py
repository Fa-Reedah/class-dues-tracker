from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, func, select

from app.db import get_session, init_db
from app.models.bank_row import BankRow


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Class Dues Tracker", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"status": "ok", "service": "class-dues-tracker"}


@app.get("/health")
def health():
    return {"healthy": True}


@app.get("/bank_rows/count")
def count_bank_rows(session: Session = Depends(get_session)):
    total = session.exec(select(func.count(BankRow.id))).one()
    return {"count": total}
