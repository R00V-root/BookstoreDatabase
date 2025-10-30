"""Synthetic dataset generator for the bookstore."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from faker import Faker

TIERS = {
    "dev": 1000,
    "functional": 50000,
    "performance": 1000000,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic bookstore data")
    parser.add_argument("tier", choices=TIERS.keys())
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("seed/output"),
        help="Directory where CSV files will be written",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    faker = Faker()
    Faker.seed(args.seed)
    random.seed(args.seed)
    rows = TIERS[args.tier]
    output_dir = args.output / args.tier
    output_dir.mkdir(parents=True, exist_ok=True)

    customers_path = output_dir / "customers.csv"
    with customers_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["first_name", "last_name", "email", "phone"])
        for _ in range(rows):
            writer.writerow(
                [faker.first_name(), faker.last_name(), faker.unique.email(), faker.phone_number()]
            )

    authors_path = output_dir / "authors.csv"
    with authors_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["first_name", "last_name", "biography"])
        for _ in range(max(rows // 10, 10)):
            writer.writerow([
                faker.first_name(),
                faker.last_name(),
                faker.paragraph(nb_sentences=3),
            ])

    publishers_path = output_dir / "publishers.csv"
    with publishers_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name", "website", "email"])
        for _ in range(max(rows // 20, 5)):
            writer.writerow(
                [faker.company(), faker.url(), faker.company_email()]
            )

    books_path = output_dir / "books.csv"
    with books_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["isbn", "title", "description", "price", "currency"])
        for _ in range(rows // 2):
            writer.writerow(
                [
                    faker.isbn13(separator=""),
                    faker.sentence(nb_words=5),
                    faker.paragraph(nb_sentences=2),
                    round(random.uniform(5, 90), 2),
                    "USD",
                ]
            )

    inventory_path = output_dir / "inventory.csv"
    with inventory_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["isbn", "warehouse_code", "quantity"])
        for _ in range(rows):
            writer.writerow([
                faker.isbn13(separator=""),
                f"WH-{random.randint(1,5)}",
                random.randint(0, 200),
            ])

    print(f"Generated synthetic dataset in {output_dir}")


if __name__ == "__main__":
    main()
