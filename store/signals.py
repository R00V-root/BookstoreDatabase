from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.db import transaction


EMPLOYEE_PERMS = [
    "add_order",
    "change_order",
    "view_order",
    "add_orderline",
    "change_orderline",
    "view_orderline",
]

ADMIN_PERMS = "__all__"


@transaction.atomic
def create_default_groups(sender, **kwargs):
    employee_group, _ = Group.objects.get_or_create(name="Employee")
    admin_group, _ = Group.objects.get_or_create(name="Admin")

    employee_group.permissions.clear()
    if ADMIN_PERMS == "__all__":
        admin_group.permissions.set(Permission.objects.all())
    else:
        admin_group.permissions.clear()

    perms = Permission.objects.filter(content_type__app_label="store", codename__in=EMPLOYEE_PERMS)
    employee_group.permissions.set(perms)
