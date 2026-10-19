from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: int | None = Field(default=None, primary_key=True)
