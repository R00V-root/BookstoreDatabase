from __future__ import annotations

from django.core.management.base import BaseCommand

from store.signals import create_default_groups


class Command(BaseCommand):
    help = "Ensure Employee and Admin groups exist with correct permissions"

    def handle(self, *args, **options):  # type: ignore[override]
        create_default_groups(sender=self)
        self.stdout.write(self.style.SUCCESS("Groups synced."))
