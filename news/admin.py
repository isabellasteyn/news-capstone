"""Django admin configuration for news models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, CustomUser, Newsletter, Publisher


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Add news role and subscription fields to Django's user admin."""

    fieldsets = [
        *(UserAdmin.fieldsets or []),
        (
            "News role",
            {
                "fields": (
                    "role",
                    "publisher_subscriptions",
                    "journalist_subscriptions",
                ),
            },
        ),
    ]

    add_fieldsets = [
        *(UserAdmin.add_fieldsets or []),
        (
            "News role",
            {"fields": ("role",)},
        ),
    ]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Make publisher staff relationships easy to manage."""

    list_display = ["name"]
    filter_horizontal = ["editors", "journalists"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Show article approval and publisher information in admin."""

    list_display = ["title", "author", "publisher", "approved"]
    list_filter = ["approved", "publisher"]


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Show newsletter publisher and author information in admin."""

    list_display = ["title", "author", "publisher", "created_at"]
    list_filter = ["publisher"]
    filter_horizontal = ["articles"]
