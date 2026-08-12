"""Automated tests for the news application and REST API."""

from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from .models import Article, CustomUser, Publisher


class NewsModelTest(TestCase):
    """Tests for the news application models."""

    def setUp(self):
        self.journalist = CustomUser.objects.create_user(
            username="journalist",
            password="pass12345",
            role=CustomUser.JOURNALIST,
        )

        self.publisher = Publisher.objects.create(
            name="Daily Student"
        )

        self.publisher.journalists.add(self.journalist)

        self.article = Article.objects.create(
            title="Test Article",
            content="Test article content.",
            author=self.journalist,
            publisher=self.publisher,
        )

    def test_article_has_title_and_content(self):
        """Article stores its title and content."""
        article = Article.objects.get(id=self.article.pk)

        self.assertEqual(article.title, "Test Article")
        self.assertEqual(
            article.content,
            "Test article content.",
        )

    def test_article_starts_unapproved(self):
        """New articles should require editor approval."""
        self.assertFalse(self.article.approved)

    def test_role_groups_exist_after_migrations(self):
        """Required user groups should exist."""
        self.assertTrue(
            Group.objects.filter(name="Reader").exists()
        )
        self.assertTrue(
            Group.objects.filter(name="Editor").exists()
        )
        self.assertTrue(
            Group.objects.filter(name="Journalist").exists()
        )

    def test_user_role_assigns_matching_group(self):
        """A journalist should belong to the Journalist group."""
        self.assertTrue(
            self.journalist.groups.filter(
                name="Journalist"
            ).exists()
        )

    def test_journalist_group_has_article_create_permission(self):
        """Journalists should be allowed to create articles."""
        self.assertTrue(
            self.journalist.has_perm("news.add_article")
        )

    def test_journalist_cannot_use_unaffiliated_publisher(self):
        """Journalists cannot publish for unrelated publishers."""
        other_publisher = Publisher.objects.create(
            name="Other Publisher"
        )

        article = Article(
            title="Wrong Publisher",
            content="Test",
            author=self.journalist,
            publisher=other_publisher,
        )

        with self.assertRaises(ValidationError):
            article.full_clean()


class NewsViewTest(TestCase):
    """Tests for normal Django page views."""

    def setUp(self):
        self.journalist = CustomUser.objects.create_user(
            username="journalist",
            password="pass12345",
            role=CustomUser.JOURNALIST,
        )

        Article.objects.create(
            title="Approved Article",
            content="Visible content",
            author=self.journalist,
            approved=True,
        )

    def test_article_list_view(self):
        """Approved articles should appear on the home page."""
        response = self.client.get(
            reverse("article_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Approved Article",
        )

    def test_article_detail_view(self):
        """An approved article should have a detail page."""
        article = Article.objects.get(
            title="Approved Article"
        )

        response = self.client.get(
            reverse(
                "article_detail",
                args=[article.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Visible content",
        )


class RegistrationTest(TestCase):
    """Tests for user registration."""

    def test_short_password_shows_validation_error(self):
        """Passwords shorter than eight characters are rejected."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "shortpassuser",
                "email": "short@example.com",
                "role": CustomUser.READER,
                "password1": "abc123",
                "password2": "abc123",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "at least 8 characters",
        )

        self.assertFalse(
            CustomUser.objects.filter(
                username="shortpassuser"
            ).exists()
        )

    def test_valid_password_creates_user(self):
        """A valid password should create the account."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "validuser",
                "email": "valid@example.com",
                "role": CustomUser.READER,
                "password1": "validpass123",
                "password2": "validpass123",
            },
        )

        self.assertRedirects(
            response,
            reverse("article_list"),
        )

        self.assertTrue(
            CustomUser.objects.filter(
                username="validuser"
            ).exists()
        )


class NewsAPITest(APITestCase):
    """Tests for the REST API."""

    api_client: APIClient

    def setUp(self):
        self.api_client = APIClient()

        # Create users for each role.
        self.reader = CustomUser.objects.create_user(
            username="reader",
            password="pass12345",
            role=CustomUser.READER,
        )

        self.journalist = CustomUser.objects.create_user(
            username="journalist",
            password="pass12345",
            role=CustomUser.JOURNALIST,
        )

        self.other_journalist = CustomUser.objects.create_user(
            username="other_journalist",
            password="pass12345",
            role=CustomUser.JOURNALIST,
        )

        self.editor = CustomUser.objects.create_user(
            username="editor",
            password="pass12345",
            role=CustomUser.EDITOR,
        )

        # Create two unrelated publishers.
        self.subscribed_publisher = Publisher.objects.create(
            name="Subscribed News"
        )

        self.other_publisher = Publisher.objects.create(
            name="Other News"
        )

        # Set publisher staff.
        self.subscribed_publisher.journalists.add(
            self.journalist
        )

        self.subscribed_publisher.editors.add(
            self.editor
        )

        self.other_publisher.journalists.add(
            self.other_journalist
        )

        # Reader follows the first publisher and journalist only.
        self.reader.publisher_subscriptions.add(
            self.subscribed_publisher
        )

        self.reader.journalist_subscriptions.add(
            self.journalist
        )

        # Article from a subscribed source.
        self.subscribed_article = Article.objects.create(
            title="Subscribed Article",
            content="Subscribed content",
            author=self.journalist,
            publisher=self.subscribed_publisher,
            approved=True,
        )

        # Article from a completely unrelated source.
        self.other_article = Article.objects.create(
            title="Other Article",
            content="Other content",
            author=self.other_journalist,
            publisher=self.other_publisher,
            approved=True,
        )

        # API authentication tokens.
        self.reader_token = Token.objects.create(
            user=self.reader
        )

        self.journalist_token = Token.objects.create(
            user=self.journalist
        )

        self.editor_token = Token.objects.create(
            user=self.editor
        )

    def authenticate(self, token):
        """Authenticate the API client using a token."""
        self.api_client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_reader_can_retrieve_all_approved_articles(self):
        """Readers can retrieve all approved articles."""
        self.authenticate(self.reader_token)

        response = self.api_client.get(
            reverse("api_articles")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_reader_subscribed_endpoint_filters_articles(self):
        """Subscribed endpoint only returns followed content."""
        self.authenticate(self.reader_token)

        response = self.api_client.get(
            reverse("api_subscribed_articles")
        )

        self.assertEqual(response.status_code, 200)

        titles = [
            article["title"]
            for article in response.data
        ]

        self.assertIn(
            "Subscribed Article",
            titles,
        )

        self.assertNotIn(
            "Other Article",
            titles,
        )

    def test_unauthenticated_request_is_rejected(self):
        """Protected API endpoints require authentication."""
        response = self.api_client.get(
            reverse("api_articles")
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_journalist_can_create_article(self):
        """Journalists can create independent articles."""
        self.authenticate(self.journalist_token)

        response = self.api_client.post(
            reverse("api_articles"),
            {
                "title": "New Article",
                "content": "New content",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertFalse(
            response.data["approved"]
        )

    def test_journalist_cannot_publish_for_unaffiliated_publisher(
        self,
    ):
        """Journalists cannot use an unrelated publisher."""
        publisher = Publisher.objects.create(
            name="Unaffiliated News"
        )

        self.authenticate(
            self.journalist_token
        )

        response = self.api_client.post(
            reverse("api_articles"),
            {
                "title": "Not My Publisher",
                "content": "No",
                "publisher": publisher.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_reader_cannot_create_article(self):
        """Readers cannot create articles."""
        self.authenticate(self.reader_token)

        response = self.api_client.post(
            reverse("api_articles"),
            {
                "title": "Not Allowed",
                "content": "No",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_editor_can_update_own_publisher_article(self):
        """Editors can update articles for their publisher."""
        self.authenticate(self.editor_token)

        response = self.api_client.put(
            reverse(
                "api_article_detail",
                args=[self.subscribed_article.pk],
            ),
            {
                "title": "Updated Title",
                "content": "Updated content",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["title"],
            "Updated Title",
        )

    def test_editor_cannot_delete_other_publisher_article(self):
        """Editors cannot manage another publisher's article."""
        self.authenticate(self.editor_token)

        response = self.api_client.delete(
            reverse(
                "api_article_detail",
                args=[self.other_article.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertTrue(
            Article.objects.filter(
                id=self.other_article.pk
            ).exists()
        )

    def test_editor_can_delete_independent_article(self):
        """Any editor may manage an independent article."""
        article = Article.objects.create(
            title="Independent",
            content="Independent content",
            author=self.journalist,
            approved=True,
        )

        self.authenticate(self.editor_token)

        response = self.api_client.delete(
            reverse(
                "api_article_detail",
                args=[article.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            204,
        )

    def test_newsletter_can_be_created_by_journalist(self):
        """Journalists can create newsletters."""
        self.authenticate(self.journalist_token)

        response = self.api_client.post(
            reverse("api_newsletters"),
            {
                "title": "Weekly News",
                "description": "This week's articles",
                "publisher": self.subscribed_publisher.pk,
                "articles": [self.subscribed_article.pk],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["title"],
            "Weekly News",
        )

        self.assertEqual(
            response.data["publisher"],
            self.subscribed_publisher.pk,
        )

    def test_publisher_newsletter_rejects_other_publisher_article(self):
        """A publisher newsletter cannot mix articles from publishers."""
        self.authenticate(self.journalist_token)

        response = self.api_client.post(
            reverse("api_newsletters"),
            {
                "title": "Mixed News",
                "description": "Invalid mix",
                "publisher": self.subscribed_publisher.pk,
                "articles": [self.other_article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_independent_newsletter_accepts_own_independent_article(self):
        """A journalist can create a newsletter from own independent work."""
        article = Article.objects.create(
            title="Independent Article",
            content="Independent content",
            author=self.journalist,
            approved=True,
        )
        self.authenticate(self.journalist_token)

        response = self.api_client.post(
            reverse("api_newsletters"),
            {
                "title": "Independent Weekly",
                "description": "Independent articles",
                "articles": [article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["publisher"])

    @patch("news.signals.post_article_to_x")
    @patch("news.signals.notify_article_subscribers")
    def test_approval_triggers_notification_logic(
        self,
        notify_mock,
        x_mock,
    ):
        """Approval should trigger subscriber notifications."""
        article = Article.objects.create(
            title="Needs Approval",
            content="Approval content",
            author=self.journalist,
        )

        article.approved = True
        article.save()

        notify_mock.assert_called_once_with(
            article
        )

        x_mock.assert_called_once_with(
            article
        )

        article.refresh_from_db()

        self.assertTrue(
            article.notification_sent
        )
