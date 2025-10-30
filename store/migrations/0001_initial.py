from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

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
                ("description", models.TextField(blank=True)),
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
                ("loyalty_points", models.PositiveIntegerField(default=0)),
            ],
            options={"db_table": "customers", "ordering": ["last_name", "first_name"]},
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("line1", models.CharField(max_length=255)),
                ("line2", models.CharField(blank=True, max_length=255)),
                ("city", models.CharField(max_length=128)),
                ("state", models.CharField(max_length=128)),
                ("postal_code", models.CharField(max_length=32)),
                ("country", models.CharField(max_length=64)),
                ("is_default_shipping", models.BooleanField(default=False)),
                ("is_default_billing", models.BooleanField(default=False)),
                (
                    "customer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to="store.customer",
                    ),
                ),
            ],
            options={"db_table": "addresses"},
        ),
        migrations.AddIndex(
            model_name="address",
            index=models.Index(fields=["postal_code", "country"], name="addresses_postal_idx"),
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
                ("weight_grams", models.PositiveIntegerField(default=0)),
                ("dimensions", models.CharField(blank=True, max_length=64)),
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
            name="Warehouse",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "address",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="warehouses",
                        to="store.address",
                    ),
                ),
            ],
            options={"db_table": "warehouses"},
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="carts",
                        to="store.customer",
                    ),
                ),
            ],
            options={"db_table": "carts"},
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
                ("locked_at", models.DateTimeField(blank=True, null=True)),
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
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(choices=[("checkout", "Checkout"), ("update", "Update"), ("delete", "Delete")], max_length=32)),
                ("description", models.TextField()),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="store.order",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="auth.user",
                    ),
                ),
            ],
            options={"db_table": "audit_logs", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Inventory",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField(default=0)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory",
                        to="store.book",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory",
                        to="store.warehouse",
                    ),
                ),
            ],
            options={"db_table": "inventory", "unique_together": {("warehouse", "book")}},
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
            name="CartItem",
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
                        related_name="cart_items",
                        to="store.book",
                    ),
                ),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="store.cart",
                    ),
                ),
            ],
            options={"db_table": "cart_items", "unique_together": {("cart", "book")}},
        ),
        migrations.CreateModel(
            name="OrderAddress",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("address_type", models.CharField(choices=[("shipping", "Shipping"), ("billing", "Billing")], max_length=16)),
                (
                    "address",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_addresses",
                        to="store.address",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="addresses",
                        to="store.order",
                    ),
                ),
            ],
            options={"db_table": "order_addresses", "unique_together": {("order", "address_type")}},
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
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("payment_method", models.CharField(max_length=64)),
                ("transaction_reference", models.CharField(max_length=128, unique=True)),
                ("status", models.CharField(default="captured", max_length=32)),
                ("processed_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="store.order",
                    ),
                ),
            ],
            options={"db_table": "payments"},
        ),
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("carrier", models.CharField(max_length=64)),
                ("tracking_number", models.CharField(max_length=128, unique=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shipments",
                        to="store.order",
                    ),
                ),
            ],
            options={"db_table": "shipments"},
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rating", models.PositiveIntegerField()),
                ("comment", models.TextField(blank=True)),
                ("is_public", models.BooleanField(default=True)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="store.book",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="store.customer",
                    ),
                ),
            ],
            options={"db_table": "reviews", "unique_together": {("customer", "book")}},
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS books_search_gin ON books USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));",
            reverse_sql="DROP INDEX IF EXISTS books_search_gin;",
        ),
    ]
