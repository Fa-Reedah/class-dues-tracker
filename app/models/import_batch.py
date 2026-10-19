from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class ImportBatch(SQLModel, table=True):
    __tablename__ = "import_batch"

    id: int | None = Field(default=None, primary_key=True)
    filename: str
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_type=DateTime(timezone=False),
    )
    row_count: int = Field(default=0)
    total_credit: Decimal = Field(
        default=Decimal("0.00"), max_digits=14, decimal_places=2
    )
