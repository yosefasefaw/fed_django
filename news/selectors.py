"""
Selectors for the news app.
These functions query the local database and return Article/Source querysets.
"""

from datetime import datetime

from django.db.models import QuerySet

from core.constants import SOURCE_TITLES
from .models import Article


def get_articles_from_db(
    start_date: datetime, end_date: datetime, filter_sources: bool = False
) -> QuerySet[Article]:
    """
    Retrieves English articles within a date range.

    Args:
        start_date: Start of the date range (inclusive)
        end_date: End of the date range (inclusive)
        filter_sources: If True, only return articles from trusted sources (SOURCE_TITLES)

    Returns:
        QuerySet of Article objects
    """
    articles_qs = Article.objects.filter(
        lang="eng", published_at__range=(start_date, end_date)
    )

    if filter_sources:
        articles_qs = articles_qs.filter(source__title__in=SOURCE_TITLES)
        print(f"Filtering to {len(SOURCE_TITLES)} trusted sources")

    return articles_qs
