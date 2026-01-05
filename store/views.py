from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import DecimalField, F, Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from store.forms import BookForm, CustomerForm, OrderForm, OrderLineFormSet
from store.models import Book, Customer, Order, OrderStatus, Publisher


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


class CustomerDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Customer
    template_name = "store/customer_detail.html"
    permission_required = "store.view_customer"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["orders"] = self.object.orders.order_by("-placed_at")
        return context


class BookListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Book
    template_name = "store/book_list.html"
    permission_required = "store.view_book"
    paginate_by = 20


class BookDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Book
    template_name = "store/book_detail.html"
    permission_required = "store.view_book"

    def get_queryset(self):  # type: ignore[override]
        return (
            super()
            .get_queryset()
            .select_related("publisher")
            .prefetch_related("book_authors__author", "book_categories__category")
        )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        book = self.object

        customers = (
            Customer.objects.filter(orders__lines__book=book)
            .annotate(
                total_quantity=Sum(
                    "orders__lines__quantity", filter=Q(orders__lines__book=book)
                ),
                last_purchase=Max(
                    "orders__placed_at", filter=Q(orders__lines__book=book)
                ),
            )
            .order_by("last_name", "first_name")
        )

        orders = (
            Order.objects.filter(lines__book=book)
            .select_related("customer")
            .annotate(
                quantity=Sum("lines__quantity", filter=Q(lines__book=book)),
                subtotal=Sum(
                    F("lines__quantity") * F("lines__unit_price"),
                    filter=Q(lines__book=book),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
            .order_by("-placed_at")
        )

        context.update({"customers": customers, "orders": orders})
        return context


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
