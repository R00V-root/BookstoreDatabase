from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Author(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    biography = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["last_name", "first_name"]
        unique_together = ("first_name", "last_name")

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Publisher(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        db_table = "publishers"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Category(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Book(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    isbn = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    publication_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=32, default="EN")
    format = models.CharField(max_length=32, default="paperback")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT, related_name="books")

    class Meta:
        db_table = "books"
        indexes = [
            models.Index(fields=["title"], name="books_title_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class BookAuthor(models.Model):
    id = models.BigAutoField(primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_authors")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="author_books")
    contribution = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "book_authors"
        unique_together = ("book", "author")


class BookCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category_books")

    class Meta:
        db_table = "book_categories"
        unique_together = ("book", "category")


class Customer(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "customers"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"



class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    ALLOCATED = "ALLOCATED", "Allocated"
    SHIPPED = "SHIPPED", "Shipped"
    DELIVERED = "DELIVERED", "Delivered"
    CANCELLED = "CANCELLED", "Cancelled"
    RETURNED = "RETURNED", "Returned"


class Order(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    order_number = models.CharField(max_length=64, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    placed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["customer", "created_at"], name="orders_customer_created_idx"),
        ]

    def can_transition(self, target_status: str) -> bool:
        sequence = settings.ORDER_STATUS_SEQUENCE
        current_index = sequence.index(self.status)
        try:
            target_index = sequence.index(target_status)
        except ValueError as exc:
            raise ValidationError(f"Invalid target status {target_status}") from exc
        return target_index >= current_index or target_status == OrderStatus.CANCELLED

    def transition(self, target_status: str) -> None:
        if not self.can_transition(target_status):
            raise ValidationError("Illegal status transition")
        self.status = target_status
        self.save(update_fields=["status", "updated_at"])

class OrderLine(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_lines"
        unique_together = ("order", "book")

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price


# Signals for automatic order numbering
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Order)
def ensure_order_number(sender, instance: Order, **kwargs) -> None:
    if not instance.order_number:
        instance.order_number = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
