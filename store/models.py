from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
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
    description = models.TextField(blank=True)

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
    weight_grams = models.PositiveIntegerField(default=0)
    dimensions = models.CharField(max_length=64, blank=True)
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


class Address(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True
    )
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=64)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        db_table = "addresses"
        indexes = [models.Index(fields=["postal_code", "country"], name="addresses_postal_idx")]

    def __str__(self) -> str:
        return f"{self.line1}, {self.city}"


class Warehouse(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="warehouses")

    class Meta:
        db_table = "warehouses"

    def __str__(self) -> str:
        return self.code


class Inventory(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "inventory"
        unique_together = ("warehouse", "book")

    def allocate(self, amount: int) -> None:
        if amount < 0:
            raise ValidationError("Allocation amount cannot be negative")
        if self.quantity < amount:
            raise ValidationError("Insufficient inventory")
        self.quantity -= amount
        self.save(update_fields=["quantity", "updated_at"])


class Cart(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="carts")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "carts"

    def total_amount(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))


class CartItem(TimestampedModel):
    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="cart_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "cart_items"
        unique_together = ("cart", "book")

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price


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
    locked_at = models.DateTimeField(null=True, blank=True)

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

    @transaction.atomic
    def checkout_from_cart(self, cart: Cart, user_id: int | None = None) -> "Order":
        if not cart.items.exists():
            raise ValidationError("Cart is empty")
        self.customer = cart.customer
        self.status = OrderStatus.PENDING
        self.order_number = self.order_number or f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        self.locked_at = timezone.now()
        self.save()
        total = Decimal("0.00")
        for item in cart.items.select_related("book").all():
            inventory_rows = Inventory.objects.select_for_update().filter(book=item.book).order_by("id")
            if not inventory_rows.exists():
                raise ValidationError(f"No inventory for {item.book}")
            allocated = False
            for stock in inventory_rows:
                if stock.quantity >= item.quantity:
                    stock.allocate(item.quantity)
                    allocated = True
                    break
            if not allocated:
                raise ValidationError(f"Insufficient inventory for {item.book}")
            OrderLine.objects.create(
                order=self,
                book=item.book,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            total += item.subtotal
        self.total_amount = total
        self.status = OrderStatus.PAID
        self.save(update_fields=["total_amount", "status", "locked_at", "updated_at"])
        cart.is_active = False
        cart.save(update_fields=["is_active", "updated_at"])
        AuditLog.log("checkout", f"Order {self.order_number} created", user_id=user_id, order=self)
        return self


class OrderAddress(TimestampedModel):
    ADDRESS_TYPES = (
        ("shipping", "Shipping"),
        ("billing", "Billing"),
    )

    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=16, choices=ADDRESS_TYPES)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="order_addresses")

    class Meta:
        db_table = "order_addresses"
        unique_together = ("order", "address_type")


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


class AuditLog(TimestampedModel):
    ACTIONS = (
        ("checkout", "Checkout"),
        ("update", "Update"),
        ("delete", "Delete"),
    )

    id = models.BigAutoField(primary_key=True)
    action = models.CharField(max_length=32, choices=ACTIONS)
    description = models.TextField()
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    @classmethod
    def log(cls, action: str, description: str, *, user_id: int | None = None, order: Order | None = None) -> "AuditLog":
        return cls.objects.create(action=action, description=description, order=order, user_id=user_id)


# Signals for automatic order numbering
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Order)
def ensure_order_number(sender, instance: Order, **kwargs) -> None:
    if not instance.order_number:
        instance.order_number = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
