"""Additional API authentication smoke tests."""
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.response import Response
from typing import cast, Any
from .models import CustomUser


class TokenAuthenticationTest(APITestCase):
    def test_token_endpoint_returns_token(self):
        CustomUser.objects.create_user(
            username="reader",
            password="pass12345",
        )

        client = APIClient()
        response = cast(
            Response,
            client.post(
                reverse("api_token"),
                {"username": "reader", "password": "pass12345"},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, 200)
        data = cast(dict[str, Any], response.data)
        self.assertIn("token", data)
        self.assertIsInstance(data["token"], str)
