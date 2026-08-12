"""REST API views for the news application."""
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Article, CustomUser, Newsletter, Publisher
from .permissions import editor_can_manage_article
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def article_collection(request):
    """List approved articles or create an article as a journalist."""
    if request.method == "GET":
        articles = Article.objects.filter(approved=True)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    if request.user.role != CustomUser.JOURNALIST:
        return Response(
            {"error": "Only journalists can create articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ArticleSerializer(
        data=request.data,
        context={"request": request},
    )
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def subscribed_articles(request):
    """Return approved articles from a reader's subscriptions."""
    if request.user.role != CustomUser.READER:
        return Response(
            {"error": "Only readers have article subscriptions."},
            status=status.HTTP_403_FORBIDDEN,
        )

    articles = Article.objects.filter(approved=True).filter(
        Q(publisher__in=request.user.publisher_subscriptions.all())
        | Q(author__in=request.user.journalist_subscriptions.all())
    ).distinct()

    return Response(ArticleSerializer(articles, many=True).data)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def article_detail_api(request, pk):
    """Retrieve, update or delete one article with role checks."""
    article = Article.objects.filter(pk=pk).first()
    if article is None:
        return Response(
            {"error": "Article not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        if not article.approved:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ArticleSerializer(article).data)

    if request.user.role not in (CustomUser.EDITOR, CustomUser.JOURNALIST):
        return Response(
            {"error": "Permission denied."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.user.role == CustomUser.JOURNALIST:
        if article.author != request.user:
            return Response(
                {"error": "You can only edit your own articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
    elif not editor_can_manage_article(request.user, article):
        return Response(
            {"error": "You can only manage your publisher articles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "DELETE":
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ArticleSerializer(
        article,
        data=request.data,
        partial=True,
        context={"request": request},
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def publisher_list(request):
    """Return all publishers."""
    publishers = PublisherSerializer(Publisher.objects.all(), many=True)
    return Response(publishers.data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_list(request):
    """Return basic user information."""
    users = UserSerializer(CustomUser.objects.all(), many=True)
    return Response(users.data)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def newsletter_collection(request):
    """List newsletters or create one as an editor/journalist."""
    if request.method == "GET":
        newsletters = NewsletterSerializer(
            Newsletter.objects.all(), many=True
        )
        return Response(newsletters.data)

    if request.user.role not in (CustomUser.EDITOR, CustomUser.JOURNALIST):
        return Response(
            {"error": "Permission denied."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = NewsletterSerializer(
        data=request.data,
        context={"request": request},
    )
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
