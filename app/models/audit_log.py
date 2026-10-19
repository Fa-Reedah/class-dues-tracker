from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True)
    entity_id: int = Field(index=True)
    field: str
    old_value: str | None = None
    new_value: str | None = None
    changed_by: str
    changed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_type=DateTime(timezone=False),
    )
