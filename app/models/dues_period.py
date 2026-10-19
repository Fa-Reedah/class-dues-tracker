from datetime import date
from decimal import Decimal

from sqlmodel import Field, SQLModel


class DuesPeriod(SQLModel, table=True):
    __tablename__ = "dues_period"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    deadline: date
    active: bool = Field(default=True)


class DuesPeriodCreate(SQLModel):
    name: str
    amount: Decimal
    deadline: date
    active: bool = True


class DuesPeriodUpdate(SQLModel):
    name: str | None = None
    amount: Decimal | None = None
    deadline: date | None = None
    active: bool | None = None
