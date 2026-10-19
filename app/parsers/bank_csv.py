import csv
import hashlib
import io
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.models.bank_row import BankRow


_MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}


def _parse_trans_date(s: str) -> datetime:
    parts = s.strip().split()
    if len(parts) != 4:
        raise ValueError(f"Bad Trans. Date: {s!r}")
    day, mon, year = parts[0], parts[1], parts[2]
    hh, mm, ss = parts[3].split(":")
    return datetime(
        int(year), _MONTHS[mon], int(day), int(hh), int(mm), int(ss)
    )


def _parse_value_date(s: str) -> date:
    parts = s.strip().split()
    if len(parts) != 3:
        raise ValueError(f"Bad Value Date: {s!r}")
    day, mon, year = parts
    return date(int(year), _MONTHS[mon], int(day))


def _parse_money(s: str) -> Decimal | None:
    s = s.strip()
    if s in ("", "--"):
        return None
    return Decimal(s.replace(",", ""))


def _row_hash(raw: dict, position: int) -> str:
    content = f"{position}|" + "|".join(str(raw[k]) for k in raw)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _parse_reader(reader, batch_id: int) -> list[BankRow]:
    rows: list[BankRow] = []
    for position, raw in enumerate(reader, start=1):
        credit = _parse_money(raw["Credit(₦)"])
        if credit is None:
            continue

        rows.append(
            BankRow(
                batch_id=batch_id,
                trans_date=_parse_trans_date(raw["Trans. Date"]),
                value_date=_parse_value_date(raw["Value Date"]),
                description=raw["Description"].strip(),
                debit=_parse_money(raw["Debit(₦)"]),
                credit=credit,
                balance_after=_parse_money(raw["Balance After(₦)"]),
                channel=raw["Channel"].strip() or None,
                bank_ref=raw["Transaction Reference"].strip(),
                file_position=position,
                file_hash=_row_hash(raw, position),
            )
        )
    return rows


def parse_bank_csv(path: Path | str, batch_id: int) -> list[BankRow]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return _parse_reader(reader, batch_id)


def parse_bank_csv_text(text: str, batch_id: int) -> list[BankRow]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    return _parse_reader(reader, batch_id)
