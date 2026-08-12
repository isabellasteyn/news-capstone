"""Role-based permission helpers for HTML views."""
from functools import wraps

from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Article, CustomUser, Newsletter


def role_required(*roles):
    """Allow a view only when the current user has one of the given roles."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                message = "You do not have permission for this page."
                messages.error(request, message)
                return HttpResponseForbidden(message)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def editor_can_manage_article(user, article: Article):
    """Return True when an editor may manage the supplied article.

    Independent articles can be handled by any editor. Publisher articles
    can only be handled by editors assigned to that publisher.
    """
    if user.role != CustomUser.EDITOR:
        return False

    if article.publisher is None:
        return True

    return article.publisher.editors.filter(pk=user.pk).exists()


def editor_can_manage_newsletter(user, newsletter: Newsletter):
    """Return True for an editor assigned to the newsletter publisher."""
    if user.role != CustomUser.EDITOR or newsletter.publisher is None:
        return False

    return newsletter.publisher.editors.filter(pk=user.pk).exists()
