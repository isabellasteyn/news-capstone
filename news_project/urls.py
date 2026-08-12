"""URL configuration for the news project."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("news.urls")),
    path("api/", include("news.api_urls")),
    path("api/token/", obtain_auth_token, name="api_token"),
]
