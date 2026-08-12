"""Signals used by the news application."""

from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Article, CustomUser
from .services import notify_article_subscribers, post_article_to_x


ROLE_GROUPS = {
    CustomUser.READER: "Reader",
    CustomUser.EDITOR: "Editor",
    CustomUser.JOURNALIST: "Journalist",
}


ROLE_PERMISSIONS = {
    "Reader": [
        "view_article",
        "view_newsletter",
        "view_publisher",
    ],
    "Editor": [
        "view_article",
        "change_article",
        "delete_article",
        "view_newsletter",
        "change_newsletter",
        "delete_newsletter",
        "view_publisher",
        "change_publisher",
        "delete_publisher",
    ],
    "Journalist": [
        "add_article",
        "view_article",
        "change_article",
        "delete_article",
        "add_newsletter",
        "view_newsletter",
        "change_newsletter",
        "delete_newsletter",
        "view_publisher",
    ],
}


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """Create the default role groups after migrations finish."""
    if sender.name != "news":
        return

    for group_name, codenames in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)

        permissions = Permission.objects.filter(
            content_type__app_label="news",
            codename__in=codenames,
        )

        group.permissions.set(permissions)


@receiver(post_save, sender=CustomUser)
def sync_user_role_group(sender, instance, **kwargs):
    """Keep a user's Django group in sync with their selected role."""
    group_name = ROLE_GROUPS.get(instance.role)

    if not group_name:
        return

    group = Group.objects.filter(name=group_name).first()

    if group:
        instance.groups.set([group])


@receiver(post_save, sender=Article)
def article_approved(sender, instance, created, **kwargs):
    """Notify subscribers after an article is approved."""
    if not instance.approved or instance.notification_sent:
        return

    notify_article_subscribers(instance)

    try:
        post_article_to_x(instance)
    except Exception as error:
        # X errors should not prevent an article from being approved.
        print(f"X post failed: {error}")

    Article.objects.filter(
        pk=instance.pk,
    ).update(notification_sent=True)
