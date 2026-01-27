import os
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = "Fetch articles from Event Registry API"

    def handle(self, *args, **options):
        api_key = os.getenv("EVENTREGISTRY_API_KEY")
        if not api_key:
            self.stderr.write("EVENTREGISTRY_API_KEY not found in environment variables.")
            return

        url = "https://eventregistry.org/api/v1/article/"
        
        # Calculate dates
        end = timezone.now()
        start = end - timedelta(hours=24) # Default to last 24 hours
        
        self.stdout.write(f"Fetching articles from {start.date()} to {end.date()}...")

        payload = {
            "action": "getArticles",
            "query": {
                "$query": {
                    "$and": [
                        {
                            "$or": [
                                {
                                    "conceptUri": "http://en.wikipedia.org/wiki/Federal_funds_rate"
                                },
                                {
                                    "$and": [
                                        {
                                            "conceptUri": "http://en.wikipedia.org/wiki/Federal_Open_Market_Committee"
                                        },
                                        {
                                            "keyword": "US Federal Reserve",
                                            "keywordLoc": "body",
                                        },
                                    ]
                                },
                            ]
                        },
                        {"dateStart": start.strftime("%Y-%m-%d"), "dateEnd": end.strftime("%Y-%m-%d")}
                    ]
                },
                "$filter": {"startSourceRankPercentile": 0, "endSourceRankPercentile": 30},
            },
            "articlesPage": 1,
            "articlesCount": 5,
            "resultType": "articles",
            "articlesSortBy": "date",
            "includeArticleSocialScore": True,
            "includeArticleConcepts": True,
            "includeArticleCategories": True,
            "includeArticleLocation": True,
            "includeArticleImage": True,
            "apiKey": api_key,
        }

        headers = {"Content-Type": "application/json"}
        try:
            # Setting a timeout is good practice
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", {}).get("results", [])
            
            if not articles:
                self.stdout.write(self.style.WARNING("No articles found for the given criteria."))
                return

            self.stdout.write(self.style.SUCCESS(f"Successfully retrieved {len(articles)} articles"))
            
            for article in articles:
                self.stdout.write(f"- {article.get('title')}")
                
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Network error fetching articles: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
