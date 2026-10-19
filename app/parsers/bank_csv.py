import csv
import hashlib
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


def parse_bank_csv(path: Path | str) -> list[BankRow]:
    path = Path(path)
    rows: list[BankRow] = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for position, raw in enumerate(reader, start=1):
            credit = _parse_money(raw["Credit(₦)"])
            if credit is None:
                continue

            rows.append(
                BankRow(
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
