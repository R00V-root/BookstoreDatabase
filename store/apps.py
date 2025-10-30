from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "store"
    verbose_name = "Bookstore"

    def ready(self) -> None:  # type: ignore[override]
        from store.signals import create_default_groups

        post_migrate.connect(create_default_groups, sender=self, dispatch_uid="store.create_default_groups")
