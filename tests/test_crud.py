import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import bank_row, dues_period, payment, student  # noqa: F401


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


def test_student_create_and_list(client):
    r = client.post("/students", json={"name": "Ada", "matric": "M001"})
    assert r.status_code == 201
    assert r.json()["id"] == 1
    assert r.json()["phone"] is None

    r = client.get("/students")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_student_get_not_found(client):
    r = client.get("/students/999")
    assert r.status_code == 404


def test_student_delete(client):
    client.post("/students", json={"name": "Mary", "matric": "M003"})
    r = client.delete("/students/1")
    assert r.status_code == 204
    assert client.get("/students/1").status_code == 404


def test_student_patch(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    r = client.patch("/students/1", json={"phone": "0801"})
    assert r.status_code == 200
    assert r.json()["phone"] == "0801"
    assert r.json()["name"] == "Ada"


def test_student_patch_not_found(client):
    r = client.patch("/students/999", json={"phone": "0801"})
    assert r.status_code == 404


def test_student_import(client):
    csv_data = "name,matric,phone\nAda Obi,M001,\nChidi Eze,M002,0802\n"
    r = client.post(
        "/students/import",
        files={"file": ("students.csv", csv_data.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json() == {"created": 2, "skipped": 0, "errors": []}
    assert len(client.get("/students").json()) == 2


def test_student_import_skips_duplicates(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    csv_data = "name,matric\nAda Obi,M001\nChidi Eze,M002\n"
    r = client.post(
        "/students/import",
        files={"file": ("students.csv", csv_data.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json() == {"created": 1, "skipped": 1, "errors": []}


def test_dues_create_and_list(client):
    r = client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    assert r.status_code == 201
    assert r.json()["active"] is True

    r = client.get("/dues_periods")
    assert len(r.json()) == 1


def test_dues_get_not_found(client):
    assert client.get("/dues_periods/999").status_code == 404


def test_dues_delete(client):
    client.post(
        "/dues_periods",
        json={"name": "P2", "amount": "4000.00", "deadline": "2026-12-31"},
    )
    assert client.delete("/dues_periods/1").status_code == 204
    assert client.get("/dues_periods/1").status_code == 404


def test_dues_patch(client):
    client.post(
        "/dues_periods",
        json={"name": "P1", "amount": "3000.00", "deadline": "2026-12-31"},
    )
    r = client.patch("/dues_periods/1", json={"amount": "5000.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "5000.00"
    assert r.json()["name"] == "P1"


def test_student_duplicate_matric_returns_409(client):
    r = client.post("/students", json={"name": "A", "matric": "M001"})
    assert r.status_code == 201
    r2 = client.post("/students", json={"name": "B", "matric": "M001"})
    assert r2.status_code == 409
    assert "detail" in r2.json()


def test_dues_period_rejects_non_positive_amount(client):
    r1 = client.post(
        "/dues_periods",
        json={"name": "Zero", "amount": "0", "deadline": "2026-12-31"},
    )
    assert r1.status_code == 422

    r2 = client.post(
        "/dues_periods",
        json={"name": "Neg", "amount": "-100", "deadline": "2026-12-31"},
    )
    assert r2.status_code == 422

    r3 = client.post(
        "/dues_periods",
        json={"name": "Valid", "amount": "5000.00", "deadline": "2026-12-31"},
    )
    assert r3.status_code == 201


def test_payment_create_minimal(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    r = client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert data["source"] == "manual"
    assert data["matched_bank_row_id"] is None


def test_payment_create_missing_student(client):
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    r = client.post(
        "/payments",
        json={
            "student_id": 9999,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
        },
    )
    assert r.status_code == 400
    assert "detail" in r.json()


def test_payment_create_missing_dues_period(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    r = client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 9999,
            "amount": "5000.00",
            "date": "2026-10-20",
        },
    )
    assert r.status_code == 400
    assert "detail" in r.json()


def test_payment_duplicate_rejected(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    payload = {
        "student_id": 1,
        "dues_period_id": 1,
        "amount": "5000.00",
        "date": "2026-10-20",
        "ref": "TRF1",
    }
    r1 = client.post("/payments", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/payments", json=payload)
    assert r2.status_code == 409


def test_payment_list_all(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
            "ref": "REF1",
        },
    )
    client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-21",
            "ref": "REF2",
        },
    )
    r = client.get("/payments")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_payment_list_filter_by_student(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post("/students", json={"name": "Chidi", "matric": "M002"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
            "ref": "REF1",
        },
    )
    client.post(
        "/payments",
        json={
            "student_id": 2,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
            "ref": "REF2",
        },
    )
    r = client.get("/payments?student_id=1")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["student_id"] == 1


def test_payment_get_not_found(client):
    r = client.get("/payments/9999")
    assert r.status_code == 404


def test_payment_patch_amount(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
        },
    )
    r = client.patch("/payments/1", json={"amount": "6000.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "6000.00"
    assert r.json()["student_id"] == 1


def test_payment_delete(client):
    client.post("/students", json={"name": "Ada", "matric": "M001"})
    client.post(
        "/dues_periods",
        json={"name": "2026/27", "amount": "5000.00", "deadline": "2026-11-30"},
    )
    client.post(
        "/payments",
        json={
            "student_id": 1,
            "dues_period_id": 1,
            "amount": "5000.00",
            "date": "2026-10-20",
        },
    )
    assert client.delete("/payments/1").status_code == 204
    assert client.get("/payments/1").status_code == 404


