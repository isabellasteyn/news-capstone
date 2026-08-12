"""Forms used by the news application."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from .models import Article, CustomUser, Newsletter


class RegistrationForm(UserCreationForm):
    """Register a user and let them choose a news role."""

    class Meta:
        model = CustomUser
        fields = ["username", "email", "role", "password1", "password2"]


class ArticleForm(forms.ModelForm):
    """Create or edit an article for the supplied author."""

    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8}),
        }

    def __init__(
        self,
        *args,
        author=None,
        editor=None,
        **kwargs,
    ):
        """Set the author and limit the available publishers."""
        super().__init__(*args, **kwargs)
        publisher_field = self.fields["publisher"]
        if isinstance(publisher_field, forms.ModelChoiceField):
            publisher_field.required = False
            if author is not None:
                self.instance.author = author
                publishers = author.journalist_publishers.all()
                if editor is not None:
                    publishers = publishers.filter(
                        editors=editor
                    )
                publisher_field.queryset = publishers


class NewsletterForm(forms.ModelForm):
    """Create a newsletter with articles from one matching source."""

    class Meta:
        model = Newsletter
        fields = ["title", "description", "publisher", "articles"]

    def __init__(self, *args, author=None, user=None, **kwargs):
        """Set the author and limit publisher and article choices."""
        super().__init__(*args, **kwargs)

        if author is None:
            return

        self.instance.author = author
        user = user or author
        publisher_field = self.fields["publisher"]
        article_field = self.fields["articles"]

        if isinstance(publisher_field, forms.ModelChoiceField):
            if user.role == CustomUser.JOURNALIST:
                publisher_field.queryset = user.journalist_publishers.all()
                publisher_field.required = False
            else:
                publishers = user.editor_publishers.all()
                if author.role == CustomUser.JOURNALIST:
                    publishers = publishers.filter(journalists=author)
                publisher_field.queryset = publishers.distinct()
                publisher_field.required = True

        if isinstance(article_field, forms.ModelMultipleChoiceField):
            article_field.queryset = self._available_articles(user)
            article_field.help_text = (
                "Choose only approved articles that match the selected "
                "publisher. Independent newsletters use your own "
                "independent articles."
            )

    def _available_articles(self, user):
        """Return approved articles the user may place in a newsletter."""
        if user.role == CustomUser.EDITOR:
            return Article.objects.filter(
                approved=True,
                publisher__editors=user,
            ).distinct()

        return Article.objects.filter(
            Q(publisher__journalists=user)
            | Q(publisher__isnull=True, author=user),
            approved=True,
        ).distinct()

    def clean(self):
        """Ensure every selected article matches the newsletter publisher."""
        cleaned_data = super().clean()
        if cleaned_data is None:
            return cleaned_data
        author = getattr(self.instance, "author", None)
        publisher = cleaned_data.get("publisher")
        articles = cleaned_data.get("articles")

        if author is None or articles is None:
            return cleaned_data

        if publisher is None:
            invalid = articles.exclude(
                publisher__isnull=True,
                author=author,
            )
            if invalid.exists():
                raise forms.ValidationError(
                    "Independent newsletters can only contain your own "
                    "approved independent articles."
                )
        else:
            invalid = articles.exclude(
                publisher=publisher,
                author__journalist_publishers=publisher,
            )
            if invalid.exists():
                raise forms.ValidationError(
                    "All newsletter articles must belong to the selected "
                    "publisher and be written by its journalists."
                )

        return cleaned_data
