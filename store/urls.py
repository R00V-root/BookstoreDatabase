from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path

from store import views

urlpatterns = [
    path("login/", views.EmployeeLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("hub/", views.NavigationHubView.as_view(), name="hub"),
    path("customers/", views.CustomerListView.as_view(), name="customer-list"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/new/", views.BookCreateView.as_view(), name="book-create"),
    path("publishers/", views.PublisherListView.as_view(), name="publisher-list"),
    path("publishers/<int:pk>/", views.PublisherDetailView.as_view(), name="publisher-detail"),
    path("orders/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("orders/new/", views.InvoiceCreateView.as_view(), name="invoice-create"),
    path("orders/<int:pk>/", views.InvoiceUpdateView.as_view(), name="invoice-update"),
    path("reports/invoices/", views.InvoiceReportView.as_view(), name="invoice-report"),
    path("reports/warehouses/", views.WarehouseListView.as_view(), name="warehouse-report"),
    path("reports/warehouses/<int:pk>/", views.WarehouseDetailView.as_view(), name="warehouse-detail"),
]
