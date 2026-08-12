"""Create the Reader, Editor and Journalist groups and their permissions."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from news.models import Article, Newsletter, Publisher


class Command(BaseCommand):
    help = "Create role groups with the permissions required by the capstone."

    def handle(self, *args, **options):
        models = [Article, Newsletter, Publisher]
        permissions = {}
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions[model.__name__.lower()] = {}
            for action in ["add", "view", "change", "delete"]:
                codename = f"{action}_{model._meta.model_name}"
                permissions[model.__name__.lower()][action] = (
                    Permission.objects.get(
                        content_type=content_type,
                        codename=codename,
                    )
                )

        role_permissions = {
            "Reader": [
                permissions["article"]["view"],
                permissions["newsletter"]["view"],
                permissions["publisher"]["view"],
            ],
            "Editor": [
                permissions["article"]["view"],
                permissions["article"]["change"],
                permissions["article"]["delete"],
                permissions["newsletter"]["view"],
                permissions["newsletter"]["change"],
                permissions["newsletter"]["delete"],
                permissions["publisher"]["view"],
                permissions["publisher"]["change"],
                permissions["publisher"]["delete"],
            ],
            "Journalist": [
                permissions["article"]["add"],
                permissions["article"]["view"],
                permissions["article"]["change"],
                permissions["article"]["delete"],
                permissions["newsletter"]["add"],
                permissions["newsletter"]["view"],
                permissions["newsletter"]["change"],
                permissions["newsletter"]["delete"],
                permissions["publisher"]["view"],
            ],
        }

        for name, group_permissions in role_permissions.items():
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(group_permissions)
            self.stdout.write(self.style.SUCCESS(f"Configured {name} group."))
