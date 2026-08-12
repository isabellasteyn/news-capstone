from django.urls import path

from . import api_views

urlpatterns = [
    path(
        "articles/",
        api_views.article_collection,
        name="api_articles",
    ),
    path(
        "articles/subscribed/",
        api_views.subscribed_articles,
        name="api_subscribed_articles",
    ),
    path(
        "articles/<int:pk>/",
        api_views.article_detail_api,
        name="api_article_detail",
    ),
    path(
        "publishers/",
        api_views.publisher_list,
        name="api_publishers",
    ),
    path(
        "users/",
        api_views.user_list,
        name="api_users",
    ),
    path(
        "newsletters/",
        api_views.newsletter_collection,
        name="api_newsletters",
    ),
]
