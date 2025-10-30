from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from store.models import (
    Address,
    AuditLog,
    Book,
    Cart,
    CartItem,
    Customer,
    Inventory,
    Order,
    OrderStatus,
    Publisher,
    Warehouse,
)


@pytest.fixture
@pytest.mark.django_db
def publisher() -> Publisher:
    return Publisher.objects.create(name="Test Publisher")


@pytest.fixture
@pytest.mark.django_db
def book(publisher: Publisher) -> Book:
    return Book.objects.create(
        isbn="1234567890123",
        title="Test Book",
        price=Decimal("10.00"),
        publisher=publisher,
    )


@pytest.fixture
@pytest.mark.django_db
def customer() -> Customer:
    return Customer.objects.create(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )


@pytest.fixture
@pytest.mark.django_db
def warehouse(customer: Customer) -> Warehouse:
    address = Address.objects.create(
        line1="123 Main St",
        city="City",
        state="State",
        postal_code="12345",
        country="US",
    )
    return Warehouse.objects.create(code="WH1", name="Primary", address=address)


@pytest.fixture
@pytest.mark.django_db
def inventory(book: Book, warehouse: Warehouse) -> Inventory:
    return Inventory.objects.create(book=book, warehouse=warehouse, quantity=5)


@pytest.mark.django_db
def test_checkout_reserves_inventory(book: Book, customer: Customer, inventory: Inventory):
    cart = Cart.objects.create(customer=customer)
    CartItem.objects.create(cart=cart, book=book, quantity=2, unit_price=book.price)
    order = Order(order_number="ORD-1", customer=customer)
    order.checkout_from_cart(cart)
    inventory.refresh_from_db()
    assert inventory.quantity == 3
    assert order.total_amount == Decimal("20.00")
    assert order.status == OrderStatus.PAID


@pytest.mark.django_db
def test_checkout_fails_when_inventory_low(book: Book, customer: Customer, inventory: Inventory):
    cart = Cart.objects.create(customer=customer)
    CartItem.objects.create(cart=cart, book=book, quantity=10, unit_price=book.price)
    order = Order(order_number="ORD-2", customer=customer)
    with pytest.raises(ValidationError):
        order.checkout_from_cart(cart)


@pytest.mark.django_db
def test_audit_log_created(book: Book, customer: Customer, inventory: Inventory):
    cart = Cart.objects.create(customer=customer)
    CartItem.objects.create(cart=cart, book=book, quantity=1, unit_price=book.price)
    order = Order(order_number="ORD-3", customer=customer)
    order.checkout_from_cart(cart)
    assert AuditLog.objects.filter(order=order, action="checkout").exists()
