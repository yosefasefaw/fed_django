from django.shortcuts import render
from django.http import JsonResponse
from .models import Article

def home(request):
    """Render the main home page."""
    return render(request, "news/home.html")

def latest_article(request):
    """Return the latest article as JSON."""
    article = Article.objects.order_by("-published_at").first()
    if article:
        data = {
            "title": article.title,
            "published_at": article.published_at.strftime("%Y-%m-%d %H:%M:%S") if article.published_at else "No date",
        }
        return JsonResponse(data)
    return JsonResponse({"error": "No articles found"}, status=404)
