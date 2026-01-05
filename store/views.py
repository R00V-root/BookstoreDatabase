from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Max, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from store.forms import BookForm, CustomerForm, OrderForm, OrderLineFormSet
from store.models import Author, Book, Category, Customer, Order, OrderLine, OrderStatus, Publisher


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

    def get_queryset(self):  # type: ignore[override]
        return Customer.objects.prefetch_related(
            Prefetch(
                "orders",
                queryset=Order.objects.prefetch_related("lines__book").order_by("-placed_at"),
            )
        )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get("sort", "recent")
        ordering_options = {
            "recent": "-placed_at",
            "oldest": "placed_at",
            "spend": "-total_amount",
            "status": "status",
        }
        ordering = ordering_options.get(sort, "-placed_at")

        orders_qs = self.object.orders.prefetch_related("lines__book")
        context["orders"] = orders_qs.order_by(ordering)

        aggregates = orders_qs.aggregate(
            total_spend=Coalesce(Sum("total_amount"), Decimal("0.00")),
            order_count=Count("id"),
            average_order=Coalesce(Avg("total_amount"), Decimal("0.00")),
            last_purchase=Max("placed_at"),
        )

        context.update(
            {
                "total_spend": aggregates["total_spend"],
                "order_count": aggregates["order_count"],
                "average_order": aggregates["average_order"],
                "last_purchase": aggregates["last_purchase"],
                "current_sort": sort if sort in ordering_options else "recent",
            }
        )
        return context


class BookListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Book
    template_name = "store/book_list.html"
    permission_required = "store.view_book"


class BookDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Book
    template_name = "store/book_detail.html"
    permission_required = "store.view_book"

    def get_queryset(self):  # type: ignore[override]
        return Book.objects.select_related("publisher").prefetch_related(
            Prefetch(
                "order_lines",
                queryset=OrderLine.objects.select_related("order", "order__customer").annotate(
                    line_subtotal=F("quantity") * F("book__price")
                ).order_by("-order__placed_at"),
            )
        )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        book = self.object
        book_filter = Q(orders__lines__book=book)
        context["customer_report"] = (
            Customer.objects.filter(book_filter)
            .annotate(
                total_quantity=Coalesce(Sum("orders__lines__quantity", filter=book_filter), 0),
                last_purchase=Max("orders__lines__order__placed_at", filter=book_filter),
            )
            .order_by("last_name", "first_name")
        )
        context["order_lines"] = book.order_lines.all()
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
            for line_form in lines.forms:
                if line_form.instance.book_id:
                    line_form.instance.unit_price = line_form.instance.book.price
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
            for line_form in lines.forms:
                if line_form.instance.book_id:
                    line_form.instance.unit_price = line_form.instance.book.price
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


class SalesAnalyticsReportView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = "store/sales_report.html"
    permission_required = "store.view_order"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        line_revenue = ExpressionWrapper(
            F("category_books__book__order_lines__quantity")
            * F("category_books__book__order_lines__unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        category_revenue = (
            Category.objects.annotate(revenue=Coalesce(Sum(line_revenue), Decimal("0.00")))
            .order_by("-revenue", "name")
            .all()
        )
        author_line_revenue = ExpressionWrapper(
            F("author_books__book__order_lines__quantity")
            * F("author_books__book__order_lines__unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        author_revenue = (
            Author.objects.annotate(revenue=Coalesce(Sum(author_line_revenue), Decimal("0.00")))
            .order_by("-revenue", "last_name", "first_name")
            .all()
        )
        top_customers = (
            Customer.objects.annotate(total_spend=Coalesce(Sum("orders__total_amount"), Decimal("0.00")))
            .order_by("-total_spend", "last_name", "first_name")[:10]
        )
        context.update(
            {
                "category_revenue": category_revenue,
                "author_revenue": author_revenue,
                "top_customers": top_customers,
                "category_max": max((entry.revenue for entry in category_revenue), default=Decimal("0.00")),
                "author_max": max((entry.revenue for entry in author_revenue), default=Decimal("0.00")),
                "customer_max": max((entry.total_spend for entry in top_customers), default=Decimal("0.00")),
            }
        )
        return context
