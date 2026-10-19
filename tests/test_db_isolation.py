from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, func, select
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import payment  # noqa: F401
from app.models.bank_row import BankRow


def _make_row(suffix: str = "a") -> BankRow:
    return BankRow(
        trans_date=datetime(2026, 10, 20, 10, 0, 0),
        value_date=date(2026, 10, 20),
        description="Transfer from REDACTED",
        credit=Decimal("5000.00"),
        bank_ref=f"REF{suffix}",
        file_position=1,
        file_hash=f"hash{suffix}",
    )


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(test_engine):
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def file_engine(tmp_path):
    db_file = tmp_path / "isolation.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_session_isolation(file_engine):
    with Session(file_engine) as a:
        a.add(_make_row("a"))
        a.flush()

        with Session(file_engine) as b:
            count_b = b.exec(select(func.count(BankRow.id))).one()
            assert count_b == 0

        a.commit()

        with Session(file_engine) as c:
            count_c = c.exec(select(func.count(BankRow.id))).one()
            assert count_c == 1


def test_request_scoped_session(client, test_engine):
    r = client.get("/bank_rows/count")
    assert r.status_code == 200
    assert r.json() == {"count": 0}

    with Session(test_engine) as s:
        s.add(_make_row("x"))
        s.commit()

    r = client.get("/bank_rows/count")
    assert r.json() == {"count": 1}
