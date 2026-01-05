from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory

from store.models import Order, OrderLine


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["order_number", "customer", "status", "total_amount", "placed_at"]
        widgets = {
            "placed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


OrderLineFormSet = inlineformset_factory(
    Order,
    OrderLine,
    fields=["book", "quantity"],
    extra=1,
    can_delete=True,
)
