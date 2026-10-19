from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.parsers.bank_csv import parse_bank_csv


FIXTURE = Path(__file__).parent / "fixtures" / "bank_sample.csv"


def test_only_credit_rows_returned():
    rows = parse_bank_csv(FIXTURE)
    assert len(rows) == 4


def test_first_row_fields():
    rows = parse_bank_csv(FIXTURE)
    r = rows[0]
    assert r.credit == Decimal("320.00")
    assert r.debit is None
    assert r.trans_date == datetime(2026, 8, 18, 15, 2, 0)
    assert r.value_date == date(2026, 8, 18)
    assert r.bank_ref == "260818010100950661085745"
    assert "REDACTED" in r.description


def test_identical_amounts_kept_separate():
    rows = parse_bank_csv(FIXTURE)
    fives = [r for r in rows if r.credit == Decimal("5000.00")]
    assert len(fives) == 2
    assert fives[0].file_hash != fives[1].file_hash


def test_atm_debit_skipped():
    rows = parse_bank_csv(FIXTURE)
    assert all(r.credit > 0 for r in rows)
    assert not any("ATM WITHDRAWAL" in r.description for r in rows)
