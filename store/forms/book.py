from __future__ import annotations

from django import forms

from store.models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "description",
            "publication_date",
            "language",
            "format",
            "price",
            "currency",
            "publisher",
        ]
