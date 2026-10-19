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
