from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("first_name", models.CharField(max_length=128)),
                ("last_name", models.CharField(max_length=128)),
                ("biography", models.TextField(blank=True)),
            ],
            options={"db_table": "authors", "ordering": ["last_name", "first_name"], "unique_together": {("first_name", "last_name")}},
        ),
        migrations.CreateModel(
            name="Publisher",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("website", models.URLField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
            ],
            options={"db_table": "publishers", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=128, unique=True)),
            ],
            options={"db_table": "categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("first_name", models.CharField(max_length=128)),
                ("last_name", models.CharField(max_length=128)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone_number", models.CharField(blank=True, max_length=32)),
            ],
            options={"db_table": "customers", "ordering": ["last_name", "first_name"]},
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("isbn", models.CharField(max_length=13, unique=True)),
                ("title", models.CharField(db_index=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("language", models.CharField(default="EN", max_length=32)),
                ("format", models.CharField(default="paperback", max_length=32)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="USD", max_length=3)),
                (
                    "publisher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="books",
                        to="store.publisher",
                    ),
                ),
            ],
            options={"db_table": "books"},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order_number", models.CharField(max_length=64, unique=True)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PAID", "Paid"), ("ALLOCATED", "Allocated"), ("SHIPPED", "Shipped"), ("DELIVERED", "Delivered"), ("CANCELLED", "Cancelled"), ("RETURNED", "Returned")], default="PENDING", max_length=16)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("placed_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="store.customer",
                    ),
                ),
            ],
            options={"db_table": "orders"},
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["customer", "created_at"], name="orders_customer_created_idx"),
        ),
        migrations.CreateModel(
            name="BookAuthor",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="author_books",
                        to="store.author",
                    ),
                ),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book_authors",
                        to="store.book",
                    ),
                ),
                ("contribution", models.CharField(blank=True, max_length=128)),
            ],
            options={"db_table": "book_authors", "unique_together": {("book", "author")}},
        ),
        migrations.CreateModel(
            name="BookCategory",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book_categories",
                        to="store.book",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_books",
                        to="store.category",
                    ),
                ),
            ],
            options={"db_table": "book_categories", "unique_together": {("book", "category")}},
        ),
        migrations.CreateModel(
            name="OrderLine",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_lines",
                        to="store.book",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="store.order",
                    ),
                ),
            ],
            options={"db_table": "order_lines", "unique_together": {("order", "book")}},
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS books_search_gin ON books USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));",
            reverse_sql="DROP INDEX IF EXISTS books_search_gin;",
        ),
    ]
