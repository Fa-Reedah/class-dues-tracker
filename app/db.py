from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = "sqlite:///./class_dues.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    from app.models import audit_log, bank_row, dues_period, import_batch, payment, student  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
