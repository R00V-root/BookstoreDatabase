from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from store.forms import BookForm, CustomerForm, OrderForm, OrderLineFormSet
from store.models import Book, Customer, Inventory, Order, OrderStatus, Publisher, Shipment, Warehouse


class EmployeeLoginView(LoginView):
    template_name = "store/login.html"

    def form_valid(self, form):  # type: ignore[override]
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=username, password=password)
        if user is None:
            form.add_error(None, "Invalid credentials")
            return super().form_invalid(form)
        return super().form_valid(form)


class NavigationHubView(LoginRequiredMixin, generic.TemplateView):
    template_name = "store/hub.html"


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Customer
    template_name = "store/customer_list.html"
    permission_required = "store.view_customer"
    paginate_by = 20


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "store/customer_form.html"
    permission_required = "store.add_customer"
    success_url = reverse_lazy("customer-list")


class BookListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Book
    template_name = "store/book_list.html"
    permission_required = "store.view_book"
    paginate_by = 20


class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Book
    form_class = BookForm
    template_name = "store/book_form.html"
    permission_required = "store.add_book"
    success_url = reverse_lazy("book-list")


class PublisherListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Publisher
    template_name = "store/publisher_list.html"
    permission_required = "store.view_publisher"


class PublisherDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Publisher
    template_name = "store/publisher_detail.html"
    permission_required = "store.view_publisher"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["books"] = self.object.books.all()
        context.setdefault("book_form", BookForm(initial={"publisher": self.object}))
        return context

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        self.object = self.get_object()
        if not request.user.has_perm("store.add_book"):
            messages.error(request, "You do not have permission to add books.")
            return redirect("publisher-detail", pk=self.object.pk)
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Book added to vendor")
            return redirect("publisher-detail", pk=self.object.pk)
        context = self.get_context_data()
        context["book_form"] = form
        return self.render_to_response(context)


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Order
    template_name = "store/invoice_list.html"
    permission_required = "store.view_order"
    paginate_by = 20


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Order
    form_class = OrderForm
    template_name = "store/invoice_form.html"
    permission_required = ("store.add_order", "store.add_orderline")
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["lines"] = OrderLineFormSet(self.request.POST)
        else:
            context["lines"] = OrderLineFormSet()
        return context

    def form_valid(self, form):  # type: ignore[override]
        context = self.get_context_data()
        lines = context["lines"]
        with transaction.atomic():
            form.instance.status = OrderStatus.PAID
            if not lines.is_valid():
                return self.form_invalid(form)
            response = super().form_valid(form)
            lines.instance = self.object
            lines.save()
        messages.success(self.request, "Invoice created")
        return response


class InvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "store/invoice_form.html"
    permission_required = ("store.change_order", "store.change_orderline")
    success_url = reverse_lazy("invoice-list")

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["lines"] = OrderLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines"] = OrderLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):  # type: ignore[override]
        context = self.get_context_data()
        lines = context["lines"]
        with transaction.atomic():
            if not lines.is_valid():
                return self.form_invalid(form)
            response = super().form_valid(form)
            lines.save()
        messages.success(self.request, "Invoice updated")
        return response


class InvoiceReportView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = "store/invoice_report.html"
    permission_required = "store.view_order"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        one_week_ago = timezone.now() - timedelta(days=7)
        context["orders"] = Order.objects.filter(placed_at__gte=one_week_ago).order_by("-placed_at")
        return context


class WarehouseListView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = "store/warehouse_list.html"
    permission_required = "store.view_warehouse"
    low_stock_threshold = 5

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        warehouses = (
            Warehouse.objects.select_related("address")
            .prefetch_related(
                Prefetch(
                    "inventory",
                    queryset=Inventory.objects.select_related("book").order_by("book__title"),
                ),
                "shipments__order",
            )
            .all()
        )

        fulfillments = (
            Shipment.objects.select_related("order", "warehouse")
            .filter(warehouse__isnull=False)
            .order_by("-shipped_at", "-created_at")
        )

        orders_by_warehouse: dict[int, set[int]] = {}
        for shipment in fulfillments:
            warehouse_id = shipment.warehouse_id
            if warehouse_id is None:
                continue
            orders_by_warehouse.setdefault(warehouse_id, set()).add(shipment.order_id)

        for warehouse in warehouses:
            warehouse.fulfilled_orders_count = len(orders_by_warehouse.get(warehouse.id, set()))

        context.update(
            {
                "warehouses": warehouses,
                "low_stock_threshold": self.low_stock_threshold,
                "fulfillments": fulfillments,
            }
        )
        return context


class WarehouseDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Warehouse
    template_name = "store/warehouse_detail.html"
    permission_required = "store.view_warehouse"
    context_object_name = "warehouse"
    low_stock_threshold = 5

    def get_ordering(self) -> str:
        sort = self.request.GET.get("sort") or "title"
        sort_mapping = {
            "title": "book__title",
            "title_desc": "-book__title",
            "qty": "quantity",
            "qty_desc": "-quantity",
        }
        return sort_mapping.get(sort, "book__title")

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        inventory = (
            self.object.inventory.select_related("book")
            .order_by(self.get_ordering())
            .all()
        )
        orders = (
            Order.objects.filter(shipments__warehouse=self.object)
            .select_related("customer")
            .prefetch_related("shipments")
            .order_by("-placed_at")
            .distinct()
        )
        context.update(
            {
                "inventory": inventory,
                "orders": orders,
                "low_stock_threshold": self.low_stock_threshold,
            }
        )
        return context
