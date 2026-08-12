"""HTML views for the news application."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ArticleForm, NewsletterForm, RegistrationForm
from .models import Article, CustomUser, Newsletter, Publisher
from .permissions import (
    editor_can_manage_article,
    editor_can_manage_newsletter,
    role_required,
)


def article_list(request):
    """Show all approved articles."""
    articles = Article.objects.filter(approved=True).select_related(
        "author", "publisher"
    )
    return render(request, "news/article_list.html", {"articles": articles})


def article_detail(request, pk):
    """Show one approved article."""
    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(request, "news/article_detail.html", {"article": article})


def newsletter_list(request):
    """Show newsletters that contain at least one approved article."""
    newsletters = Newsletter.objects.filter(
        articles__approved=True
    ).select_related("author", "publisher").distinct()
    return render(
        request,
        "news/newsletter_list.html",
        {"newsletters": newsletters},
    )


def newsletter_detail(request, pk):
    """Show a newsletter and its approved articles."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    articles = newsletter.articles.filter(approved=True)
    return render(
        request,
        "news/newsletter_detail.html",
        {"newsletter": newsletter, "articles": articles},
    )


def register(request):
    """Register a user, then log them in."""
    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("article_list")

    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    """Authenticate a user with a username and password."""
    error = None

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user is not None:
            login(request, user)
            return redirect("article_list")
        error = "Invalid username or password."

    return render(request, "registration/login.html", {"error": error})


def logout_view(request):
    """Log out the current user."""
    logout(request)
    return redirect("article_list")


@login_required
@role_required(CustomUser.JOURNALIST)
def article_create(request):
    """Allow journalists to submit a new article for approval."""
    form = ArticleForm(
        request.POST or None,
        author=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Article submitted for approval.")
        return redirect("my_articles")

    return render(
        request,
        "news/article_form.html",
        {"form": form, "heading": "Create Article"},
    )


@login_required
@role_required(CustomUser.JOURNALIST)
def my_articles(request):
    """Show articles written by the current journalist."""
    articles = Article.objects.filter(author=request.user)
    return render(request, "news/my_articles.html", {"articles": articles})


@login_required
@role_required(CustomUser.EDITOR, CustomUser.JOURNALIST)
def article_update(request, pk):
    """Allow an editor or the original journalist to edit an article."""
    article = get_object_or_404(Article, pk=pk)

    if request.user.role == CustomUser.JOURNALIST:
        if article.author != request.user:
            return render(request, "news/forbidden.html", status=403)
    elif not editor_can_manage_article(request.user, article):
        return render(request, "news/forbidden.html", status=403)

    form = ArticleForm(
        request.POST or None,
        instance=article,
        author=article.author,
        editor=(
            request.user
            if request.user.role == CustomUser.EDITOR
            else None
        ),
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("my_articles")

    return render(
        request,
        "news/article_form.html",
        {"form": form, "heading": "Edit Article"},
    )


@login_required
@role_required(CustomUser.EDITOR, CustomUser.JOURNALIST)
def newsletter_create(request):
    """Allow editors and journalists to create newsletters."""
    form = NewsletterForm(
        request.POST or None,
        author=request.user,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("newsletter_list")

    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "heading": "Create Newsletter"},
    )


@login_required
@role_required(CustomUser.EDITOR, CustomUser.JOURNALIST)
def newsletter_update(request, pk):
    """Allow an editor or the original journalist to edit a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.user.role == CustomUser.JOURNALIST:
        if newsletter.author != request.user:
            return render(request, "news/forbidden.html", status=403)
    elif not editor_can_manage_newsletter(request.user, newsletter):
        return render(request, "news/forbidden.html", status=403)

    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        author=newsletter.author,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("newsletter_detail", pk=pk)

    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "heading": "Edit Newsletter"},
    )


@login_required
@role_required(CustomUser.EDITOR)
def editor_articles(request):
    """Show independent and affiliated publisher articles to editors."""
    articles = Article.objects.filter(approved=False).filter(
        Q(publisher__isnull=True)
        | Q(publisher__editors=request.user)
    ).select_related("author", "publisher").distinct()
    return render(
        request,
        "news/editor_articles.html",
        {"articles": articles},
    )


@login_required
@role_required(CustomUser.EDITOR)
def approve_article(request, pk):
    """Approve an independent or editor-affiliated publisher article."""
    article = get_object_or_404(Article, pk=pk)

    if not editor_can_manage_article(request.user, article):
        return render(request, "news/forbidden.html", status=403)

    if request.method == "POST":
        article.approved = True
        article.save()
        messages.success(request, "Article approved and notifications sent.")

    return redirect("editor_articles")


@login_required
@role_required(CustomUser.READER)
def subscriptions(request):
    """Let readers manage publisher and journalist subscriptions."""
    publishers = Publisher.objects.all()
    journalists = CustomUser.objects.filter(role=CustomUser.JOURNALIST)

    if request.method == "POST":
        request.user.publisher_subscriptions.set(
            request.POST.getlist("publishers")
        )
        request.user.journalist_subscriptions.set(
            request.POST.getlist("journalists")
        )
        messages.success(request, "Subscriptions updated.")
        return redirect("subscriptions")

    return render(
        request,
        "news/subscriptions.html",
        {"publishers": publishers, "journalists": journalists},
    )
