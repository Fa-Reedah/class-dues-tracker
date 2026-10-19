import csv
import io
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlmodel import Session, func, select

from app.db import get_session, init_db
from app.models.bank_row import BankRow
from app.models.dues_period import DuesPeriod, DuesPeriodCreate, DuesPeriodUpdate
from app.models.student import Student, StudentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Class Dues Tracker", version="0.1.0", lifespan=lifespan)


def _as_dict(model) -> dict:
    return model.model_dump(exclude_unset=True) if hasattr(model, "model_dump") else model.dict(exclude_unset=True)


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


@app.post("/students", response_model=Student, status_code=201)
def create_student(payload: Student, session: Session = Depends(get_session)):
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return payload


@app.get("/students", response_model=list[Student])
def list_students(session: Session = Depends(get_session)):
    return session.exec(select(Student)).all()


@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.patch("/students/{student_id}", response_model=Student)
def update_student(student_id: int, payload: StudentUpdate, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in _as_dict(payload).items():
        setattr(student, key, value)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()


@app.post("/students/import")
async def import_students(file: UploadFile = File(...), session: Session = Depends(get_session)):
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 CSV")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    skipped = 0
    errors: list[str] = []
    for row_num, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        matric = (row.get("matric") or "").strip()
        phone = (row.get("phone") or "").strip() or None
        if not name or not matric:
            errors.append(f"row {row_num}: missing name or matric")
            continue
        existing = session.exec(select(Student).where(Student.matric == matric)).first()
        if existing:
            skipped += 1
            continue
        session.add(Student(name=name, matric=matric, phone=phone))
        created += 1
    session.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


@app.post("/dues_periods", response_model=DuesPeriod, status_code=201)
def create_dues_period(payload: DuesPeriodCreate, session: Session = Depends(get_session)):
    period = DuesPeriod(**_as_dict(payload))
    session.add(period)
    session.commit()
    session.refresh(period)
    return period


@app.get("/dues_periods", response_model=list[DuesPeriod])
def list_dues_periods(session: Session = Depends(get_session)):
    return session.exec(select(DuesPeriod)).all()


@app.get("/dues_periods/{period_id}", response_model=DuesPeriod)
def get_dues_period(period_id: int, session: Session = Depends(get_session)):
    period = session.get(DuesPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Dues period not found")
    return period


@app.patch("/dues_periods/{period_id}", response_model=DuesPeriod)
def update_dues_period(period_id: int, payload: DuesPeriodUpdate, session: Session = Depends(get_session)):
    period = session.get(DuesPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Dues period not found")
    for key, value in _as_dict(payload).items():
        setattr(period, key, value)
    session.add(period)
    session.commit()
    session.refresh(period)
    return period


@app.delete("/dues_periods/{period_id}", status_code=204)
def delete_dues_period(period_id: int, session: Session = Depends(get_session)):
    period = session.get(DuesPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Dues period not found")
    session.delete(period)
    session.commit()
