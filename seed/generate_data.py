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
        authors = [
            (
                faker.first_name(),
                faker.last_name(),
                faker.paragraph(nb_sentences=3),
            )
            for _ in range(max(rows // 10, 10))
        ]
        writer.writerows(authors)

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
        books = [
            (
                faker.isbn13(separator=""),
                faker.sentence(nb_words=5),
                faker.paragraph(nb_sentences=2),
                round(random.uniform(5, 90), 2),
                "USD",
            )
            for _ in range(rows // 2)
        ]
        writer.writerows(books)

    categories = [
        "Fantasy",
        "Sci-Fi",
        "Romance",
        "Mystery",
        "Horror",
        "Historical Fiction",
        "Biography",
        "History",
        "Self-Help",
        "Science",
    ]
    categories_path = output_dir / "categories.csv"
    with categories_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["name", "description"])
        for category in categories:
            writer.writerow([category, faker.sentence(nb_words=8)])

    book_authors_path = output_dir / "book_authors.csv"
    with book_authors_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["isbn", "author_first_name", "author_last_name", "contribution"])
        book_isbns = [book[0] for book in books]
        random.shuffle(book_isbns)
        for first_name, last_name, _ in authors:
            books_per_author = random.randint(7, 9)
            selections = random.sample(book_isbns, min(books_per_author, len(book_isbns)))
            for isbn in selections:
                writer.writerow([isbn, first_name, last_name, "Author"])

    book_categories_path = output_dir / "book_categories.csv"
    with book_categories_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["isbn", "category"])
        book_isbns = [book[0] for book in books]
        category_assignments = {category: set() for category in categories}
        for category in categories:
            selections = random.sample(book_isbns, min(20, len(book_isbns)))
            category_assignments[category].update(selections)
        for isbn in book_isbns:
            category = random.choice(categories)
            category_assignments[category].add(isbn)
        for category, isbns in category_assignments.items():
            for isbn in sorted(isbns):
                writer.writerow([isbn, category])

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
