"""DRF serializers for turning news models into JSON data."""
from rest_framework import serializers

from .models import Article, CustomUser, Newsletter, Publisher


class UserSerializer(serializers.ModelSerializer):
    """Serialize basic user information."""

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "role"]


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher details."""

    class Meta:
        model = Publisher
        fields = ["id", "name", "description"]


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize articles with readable author and publisher names."""

    author_name = serializers.CharField(
        source="author.username", read_only=True
    )
    publisher_name = serializers.CharField(
        source="publisher.name", read_only=True
    )

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "author_name",
            "publisher",
            "publisher_name",
            "created_at",
            "approved",
        ]
        read_only_fields = ["author", "created_at", "approved"]

    def validate_publisher(self, publisher):
        """Check journalist and editor publisher affiliations."""
        request = self.context.get("request")

        if publisher is None or request is None:
            return publisher

        user = request.user
        author = (
            self.instance.author
            if self.instance is not None
            else user
        )

        if not publisher.journalists.filter(pk=author.pk).exists():
            raise serializers.ValidationError(
                "The journalist is not affiliated with this publisher."
            )

        if (
            user.role == CustomUser.EDITOR
            and not publisher.editors.filter(pk=user.pk).exists()
        ):
            raise serializers.ValidationError(
                "You can only use a publisher you edit for."
            )

        return publisher


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters and enforce matching publisher articles."""

    publisher_name = serializers.CharField(
        source="publisher.name", read_only=True
    )

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "publisher",
            "publisher_name",
            "articles",
        ]
        read_only_fields = ["author", "created_at"]

    def validate(self, attrs):
        """Validate publisher affiliation and newsletter articles."""
        request = self.context.get("request")

        if request is None:
            return attrs

        user = request.user
        publisher = attrs.get(
            "publisher",
            getattr(self.instance, "publisher", None),
        )
        articles = attrs.get("articles", [])

        self._validate_affiliation(user, publisher)
        self._validate_articles(user, publisher, articles)

        return attrs

    @staticmethod
    def _validate_affiliation(user, publisher):
        """Check that the user may use the selected publisher."""
        if user.role == CustomUser.EDITOR:
            if publisher is None or not publisher.editors.filter(
                pk=user.pk
            ).exists():
                raise serializers.ValidationError(
                    "Editors must use one of their affiliated publishers."
                )

        elif user.role == CustomUser.JOURNALIST:
            if publisher and not publisher.journalists.filter(
                pk=user.pk
            ).exists():
                raise serializers.ValidationError(
                    "You are not affiliated with this publisher."
                )

    @staticmethod
    def _validate_articles(user, publisher, articles):
        """Check the approval and ownership of selected articles."""
        for article in articles:
            if not article.approved:
                raise serializers.ValidationError(
                    "Newsletters can only contain approved articles."
                )

            if publisher is None:
                if article.publisher is not None or article.author != user:
                    raise serializers.ValidationError(
                        "Independent newsletters can only contain your own "
                        "independent articles."
                    )

            elif (
                article.publisher != publisher
                or not publisher.journalists.filter(
                    pk=article.author.pk
                ).exists()
            ):
                raise serializers.ValidationError(
                    "Newsletter articles must belong to the selected "
                    "publisher."
                )
