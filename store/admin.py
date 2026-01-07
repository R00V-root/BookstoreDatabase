from __future__ import annotations

from django.contrib import admin

from store.models import (
    Address,
    Author,
    AuditLog,
    Book,
    BookAuthor,
    BookCategory,
    Cart,
    CartItem,
    Category,
    Customer,
    Inventory,
    Order,
    OrderLine,
    Publisher,
    Warehouse,
)


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "status", "total_amount", "placed_at")
    list_filter = ("status", "placed_at")
    search_fields = ("order_number", "customer__email")
    inlines = [OrderLineInline]


admin.site.register([
    Author,
    Publisher,
    Category,
    Book,
    BookAuthor,
    BookCategory,
    Customer,
    Address,
    Warehouse,
    Inventory,
    Cart,
    CartItem,
    AuditLog,
])
