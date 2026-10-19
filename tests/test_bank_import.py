from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import audit_log, bank_row, dues_period, import_batch, payment, student  # noqa: F401


FIXTURE = Path(__file__).parent / "fixtures" / "bank_sample.csv"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def test_bank_import_success(client):
    with FIXTURE.open("rb") as f:
        r = client.post(
            "/bank_rows/import",
            files={"file": ("bank_sample.csv", f, "text/csv")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 4
    assert data["skipped"] == 0
    assert data["errors"] == []

    batch_id = data["batch_id"]
    batch_res = client.get(f"/bank_import_batches/{batch_id}")
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["row_count"] == 4
    assert Decimal(str(batch_data["total_credit"])) == Decimal("13320.00")


def test_bank_import_reimport_skips_duplicates(client):
    with FIXTURE.open("rb") as f:
        client.post(
            "/bank_rows/import",
            files={"file": ("bank_sample.csv", f, "text/csv")},
        )

    with FIXTURE.open("rb") as f:
        r = client.post(
            "/bank_rows/import",
            files={"file": ("bank_sample.csv", f, "text/csv")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 0
    assert data["skipped"] == 4

    batch_id = data["batch_id"]
    batch_data = client.get(f"/bank_import_batches/{batch_id}").json()
    assert batch_data["row_count"] == 0
    assert Decimal(str(batch_data["total_credit"])) == Decimal("0.00")


def test_bank_import_malformed_encoding(client):
    bad_bytes = b"\xff\xfe\x00\x00invalid"
    r = client.post(
        "/bank_rows/import",
        files={"file": ("bad.csv", bad_bytes, "text/csv")},
    )
    assert r.status_code == 400


def test_bank_import_batches_list(client):
    with FIXTURE.open("rb") as f:
        client.post(
            "/bank_rows/import",
            files={"file": ("bank1.csv", f, "text/csv")},
        )
    with FIXTURE.open("rb") as f:
        client.post(
            "/bank_rows/import",
            files={"file": ("bank2.csv", f, "text/csv")},
        )

    r = client.get("/bank_import_batches")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_bank_import_batch_not_found(client):
    r = client.get("/bank_import_batches/9999")
    assert r.status_code == 404


def test_bank_rows_filter_by_batch(client):
    with FIXTURE.open("rb") as f:
        client.post(
            "/bank_rows/import",
            files={"file": ("bank1.csv", f, "text/csv")},
        )
    r1 = client.get("/bank_rows?batch_id=1")
    assert r1.status_code == 200
    assert len(r1.json()) == 4

    r2 = client.get("/bank_rows?batch_id=999")
    assert r2.status_code == 200
    assert len(r2.json()) == 0
