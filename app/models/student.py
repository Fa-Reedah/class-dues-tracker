from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):
    __tablename__ = "student"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    matric: str = Field(index=True, unique=True)
    phone: str | None = Field(default=None, index=True, unique=True)
    score: int = Field(default=0)


class StudentUpdate(SQLModel):
    name: str | None = None
    matric: str | None = None
    phone: str | None = None
    score: int | None = None
