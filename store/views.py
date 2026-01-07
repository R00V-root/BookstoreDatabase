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
from store.models import (
    Author,
    Book,
    Category,
    Customer,
    Order,
    OrderLine,
    OrderStatus,
    Publisher,
)


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

    def get_queryset(self):  # type: ignore[override]
        queryset = Book.objects.select_related("publisher").prefetch_related(
            "book_authors__author",
            "book_categories__category",
        )
        publisher_id = self.request.GET.get("publisher")
        author_id = self.request.GET.get("author")
        category_id = self.request.GET.get("category")
        if publisher_id:
            queryset = queryset.filter(publisher_id=publisher_id)
        if author_id:
            queryset = queryset.filter(book_authors__author_id=author_id)
        if category_id:
            queryset = queryset.filter(book_categories__category_id=category_id)

        return queryset.distinct()

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "publishers": Publisher.objects.order_by("name"),
                "authors": Author.objects.order_by("last_name", "first_name"),
                "categories": Category.objects.order_by("name"),
                "selected_publisher": self.request.GET.get("publisher", ""),
                "selected_author": self.request.GET.get("author", ""),
                "selected_category": self.request.GET.get("category", ""),
            }
        )
        return context


class BookDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Book
    template_name = "store/book_detail.html"
    permission_required = "store.view_book"

    def get_queryset(self):  # type: ignore[override]
        return Book.objects.select_related("publisher").prefetch_related(
            "book_authors__author",
            "book_categories__category",
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

    def get_queryset(self):  # type: ignore[override]
        queryset = Publisher.objects.all()
        category_id = self.request.GET.get("category")
        author_id = self.request.GET.get("author")

        if category_id:
            queryset = queryset.filter(books__book_categories__category_id=category_id)
        if author_id:
            queryset = queryset.filter(books__book_authors__author_id=author_id)
        return queryset.distinct()

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "categories": Category.objects.order_by("name"),
                "authors": Author.objects.order_by("last_name", "first_name"),
                "selected_category": self.request.GET.get("category", ""),
                "selected_author": self.request.GET.get("author", ""),
            }
        )
        return context


class PublisherDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Publisher
    template_name = "store/publisher_detail.html"
    permission_required = "store.view_publisher"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["books"] = self.object.books.prefetch_related(
            "book_authors__author",
            "book_categories__category",
        )
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
        customer_totals = (
            Customer.objects.annotate(total_spend=Coalesce(Sum("orders__total_amount"), Decimal("0.00")))
            .order_by("-total_spend", "last_name", "first_name")[:10]
        )
        total_customer_spend = sum((customer.total_spend for customer in customer_totals), Decimal("0.00"))
        customer_spend = [
            {
                "customer": customer,
                "total_spend": customer.total_spend,
                "share_percent": (
                    (customer.total_spend / total_customer_spend) * Decimal("100.0")
                    if total_customer_spend
                    else Decimal("0.0")
                ),
            }
            for customer in customer_totals
        ]
        vendor_line_revenue = ExpressionWrapper(
            F("books__order_lines__quantity") * F("books__order_lines__unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        vendor_totals = (
            Publisher.objects.annotate(revenue=Coalesce(Sum(vendor_line_revenue), Decimal("0.00")))
            .order_by("-revenue", "name")
            .all()
        )
        total_vendor_spend = sum((vendor.revenue for vendor in vendor_totals), Decimal("0.00"))
        vendor_revenue = [
            {
                "vendor": vendor,
                "revenue": vendor.revenue,
                "share_percent": (
                    (vendor.revenue / total_vendor_spend) * Decimal("100.0")
                    if total_vendor_spend
                    else Decimal("0.0")
                ),
            }
            for vendor in vendor_totals
        ]
        context.update(
            {
                "top_customers": customer_spend,
                "vendor_revenue": vendor_revenue,
            }
        )
        return context


class AuthorListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Author
    template_name = "store/author_list.html"
    permission_required = "store.view_author"

    def get_queryset(self):  # type: ignore[override]
        queryset = Author.objects.annotate(book_count=Count("author_books", distinct=True))
        publisher_id = self.request.GET.get("publisher")
        category_id = self.request.GET.get("category")

        if publisher_id:
            queryset = queryset.filter(author_books__book__publisher_id=publisher_id)
        if category_id:
            queryset = queryset.filter(author_books__book__book_categories__category_id=category_id)
        return queryset.distinct()

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "publishers": Publisher.objects.order_by("name"),
                "categories": Category.objects.order_by("name"),
                "selected_publisher": self.request.GET.get("publisher", ""),
                "selected_category": self.request.GET.get("category", ""),
            }
        )
        return context


class AuthorDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Author
    template_name = "store/author_detail.html"
    permission_required = "store.view_author"

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        book_qs = (
            Book.objects.filter(book_authors__author=self.object)
            .select_related("publisher")
            .prefetch_related("book_categories__category")
        )
        context["books"] = book_qs
        context["categories"] = Category.objects.filter(
            category_books__book__book_authors__author=self.object
        ).distinct()
        return context

