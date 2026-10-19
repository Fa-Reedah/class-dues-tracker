from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class BankRow(SQLModel, table=True):
    __tablename__ = "bank_row"

    id: int | None = Field(default=None, primary_key=True)

    batch_id: int = Field(foreign_key="import_batch.id", index=True)
    trans_date: datetime = Field(sa_type=DateTime(timezone=False))
    value_date: date
    description: str
    debit: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    credit: Decimal = Field(max_digits=14, decimal_places=2)
    balance_after: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    channel: str | None = None
    bank_ref: str

    file_position: int
    file_hash: str = Field(index=True, unique=True)

    matched_payment_id: int | None = Field(
        default=None,
        foreign_key="payment.id",
        unique=True,
    )
