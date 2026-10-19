from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    dues_period_id: int = Field(foreign_key="dues_period.id", index=True)
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    date: date_type
    ref: str | None = Field(default=None)
    bank: str | None = Field(default=None)
    source: str = Field(default="manual")
    status: str = Field(default="pending")
    matched_bank_row_id: int | None = Field(default=None, unique=True)
    date_delta_days: int | None = Field(default=None)
    match_confidence: str | None = Field(default=None)
    match_reason: str | None = Field(default=None)
    matched_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=False))
    matched_by: str | None = Field(default=None)
    confirmed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=False))


class PaymentCreate(SQLModel):
    student_id: int
    dues_period_id: int
    amount: Decimal = Field(gt=0)
    date: date_type
    ref: str | None = None
    bank: str | None = None
    source: Literal["manual", "dva"] = "manual"
    status: Literal["pending", "confirmed", "unmatched", "suspicious"] = "pending"


class PaymentUpdate(SQLModel):
    amount: Decimal | None = Field(default=None, gt=0)
    date: date_type | None = None
    ref: str | None = None
    bank: str | None = None
    source: Literal["manual", "dva"] | None = None
    status: Literal["pending", "confirmed", "unmatched", "suspicious"] | None = None
