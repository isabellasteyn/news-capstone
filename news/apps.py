"""Application configuration for the news app."""
from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Load the news app and its signal handlers."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """Import signals when Django finishes loading the app."""
        import news.signals  # noqa: F401
