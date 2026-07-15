from __future__ import annotations

import csv
from pathlib import Path
from random import choice, randint, uniform

from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "transactions.csv"

fake = Faker()

CATEGORIES = [
    "Groceries",
    "Dining",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Health",
    "Shopping",
    "Subscriptions",
    "Travel",
    "Housing",
]

MERCHANTS = [
    "Whole Foods",
    "Starbucks",
    "Uber",
    "Spotify",
    "Target",
    "CVS",
    "Netflix",
    "Delta",
    "Amazon",
    "Verizon",
    "City Water",
    "Shell",
    "Walmart",
    "Trader Joe's",
    "Airbnb",
]


def build_rows(count: int = 250) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, count + 1):
        amount = round(uniform(3.5, 450.0), 2)
        is_income = index % 13 == 0
        if is_income:
            amount = round(abs(amount) + 1200.0, 2)
            description = f"Income from {choice(['Freelance Contract', 'Salary', 'Refund', 'Bonus'])}"
            category = "Income"
            merchant = choice(["Payroll", "Client Payment", "Reimbursement"])
        else:
            description = fake.catch_phrase()
            category = choice(CATEGORIES)
            merchant = choice(MERCHANTS)
        rows.append(
            {
                "transaction_id": f"TXN-{index:03d}",
                "date": fake.date_between(start_date="-180d", end_date="today").strftime("%Y-%m-%d"),
                "description": description,
                "amount": amount,
                "category": category,
                "merchant": merchant,
            }
        )
    return rows


def write_transactions(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["transaction_id", "date", "description", "amount", "category", "merchant"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = build_rows(250)
    write_transactions(rows, OUTPUT_PATH)
    print(f"Wrote {len(rows)} transactions to {OUTPUT_PATH}")
