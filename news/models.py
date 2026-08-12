"""Models for the student news application."""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class Publisher(models.Model):
    """A publication that can have editors and journalists."""

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        "CustomUser", related_name="editor_publishers", blank=True
    )
    journalists = models.ManyToManyField(
        "CustomUser", related_name="journalist_publishers", blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """User with a simple Reader, Editor or Journalist role."""

    READER = "reader"
    EDITOR = "editor"
    JOURNALIST = "journalist"

    ROLE_CHOICES = [
        (READER, "Reader"),
        (EDITOR, "Editor"),
        (JOURNALIST, "Journalist"),
    ]

    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=READER
    )
    publisher_subscriptions = models.ManyToManyField(
        Publisher, related_name="subscribers", blank=True
    )
    journalist_subscriptions = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="reader_subscribers",
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_reader(self):
        return self.role == self.READER

    def is_editor(self):
        return self.role == self.EDITOR

    def is_journalist(self):
        return self.role == self.JOURNALIST


class Article(models.Model):
    """A news article written by a journalist."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="articles"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        """Validate the journalist and optional publisher relationship."""
        author = getattr(self, "author", None)

        if author is None:
            return

        if author.role != CustomUser.JOURNALIST:
            raise ValidationError(
                "Articles must be authored by a journalist."
            )

        if self.publisher and not self.publisher.journalists.filter(
            pk=author.pk
        ).exists():
            raise ValidationError(
                "A journalist can only publish for an affiliated publisher."
            )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """A curated collection of articles for a publisher or journalist."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="newsletters"
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(
        Article, related_name="newsletters", blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        """Validate who may create a publisher or independent newsletter."""
        author = getattr(self, "author", None)
        publisher = getattr(self, "publisher", None)

        if author is None:
            return

        if author.role == CustomUser.JOURNALIST:
            if publisher and not publisher.journalists.filter(
                pk=author.pk
            ).exists():
                raise ValidationError(
                    "A journalist can only create newsletters for an "
                    "affiliated publisher."
                )
            return

        if author.role == CustomUser.EDITOR:
            if publisher is None:
                raise ValidationError(
                    "Editors must create newsletters for a publisher."
                )
            if not publisher.editors.filter(pk=author.pk).exists():
                raise ValidationError(
                    "An editor can only create newsletters for an "
                    "affiliated publisher."
                )
            return

        raise ValidationError(
            "Newsletters must be created by a journalist or editor."
        )

    def __str__(self):
        return self.title
