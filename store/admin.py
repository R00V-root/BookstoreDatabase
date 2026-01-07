from __future__ import annotations

from django.contrib import admin

from store.models import (
    Author,
    Book,
    BookAuthor,
    BookCategory,
    Category,
    Customer,
    Order,
    OrderLine,
    Publisher,
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
])
