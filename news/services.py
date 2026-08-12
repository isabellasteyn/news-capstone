"""Services used when an article is approved."""

import requests
from django.conf import settings
from django.core.mail import send_mass_mail
from requests_oauthlib import OAuth1


def notify_article_subscribers(article):
    """Email readers who subscribed to the article source.

    :param article: The approved article.
    :type article: Article
    :return: None
    """
    readers = set(article.author.reader_subscribers.all())

    if article.publisher:
        readers.update(article.publisher.subscribers.all())

    messages = []

    for reader in readers:
        if reader.email:
            messages.append(
                (
                    f"New article: {article.title}",
                    article.content,
                    settings.DEFAULT_FROM_EMAIL,
                    [reader.email],
                )
            )

    if messages:
        send_mass_mail(
            tuple(messages),
            fail_silently=True,
        )


def post_article_to_x(article):
    """Post an approved article to X.

    :param article: The approved article to post.
    :type article: Article
    :return: The response from X, or None if credentials are missing.
    :rtype: requests.Response or None
    """

    credentials = [
        settings.X_API_KEY,
        settings.X_API_KEY_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    ]

    if not all(credentials):
        print("X post skipped: X credentials are missing.")
        return None

    auth = OAuth1(
        settings.X_API_KEY,
        settings.X_API_KEY_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    )

    text = f"{article.title} - {article.author.username}"

    if article.publisher:
        text += f" - {article.publisher.name}"

    response = requests.post(
        settings.X_POST_ENDPOINT,
        auth=auth,
        json={"text": text},
        timeout=10,
    )

    print("X API status:", response.status_code)
    print("X API response:", response.text)

    response.raise_for_status()

    return response
