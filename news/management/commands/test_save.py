from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from news.services import retrieve_articles
from news.models import Article, Source


class Command(BaseCommand):
    help = "Test fetching and saving articles to the database"

    def handle(self, *args, **options):
        self.stdout.write("Fetching articles to test database saving...")

        try:
            date_end = timezone.now()
            date_start = date_end - timedelta(hours=2)
            articles_data = retrieve_articles(
                date_start=date_start, date_end=date_end, articles_count=2
            )

            if not articles_data:
                self.stdout.write(self.style.WARNING("No articles found to save."))
                return

            saved_count = 0
            for data in articles_data:
                # 1. Handle Source
                source_data = data.get("source", {})
                source_uri = source_data.get("uri")

                source = None
                if source_uri:
                    source, _ = Source.objects.get_or_create(
                        uri=source_uri,
                        defaults={
                            "title": source_data.get("title"),
                            "data_type": source_data.get("dataType"),
                            "image": source_data.get("image"),
                        },
                    )

                # 2. Handle Article
                pub_date_str = data.get("dateTimePub")
                pub_date = parse_datetime(pub_date_str) if pub_date_str else None

                article, created = Article.objects.update_or_create(
                    uri=data.get("uri"),
                    defaults={
                        "url": data.get("url"),
                        "title": data.get("title"),
                        "body": data.get("body"),
                        "lang": data.get("lang"),
                        "data_type": data.get("dataType"),
                        "source": source,
                        "sentiment": data.get("sentiment"),
                        "relevance": data.get("relevance"),
                        "image": data.get("image"),
                        "published_at": pub_date,
                        "authors": data.get("authors"),
                        "concepts": data.get("concepts"),
                        "categories": data.get("categories"),
                        "raw_data": data,
                    },
                )

                if created:
                    saved_count += 1
                    self.stdout.write(f"✔ Saved: {article.title}")
                else:
                    self.stdout.write(f"ℹ Updated: {article.title}")

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFinished! Total new articles saved: {saved_count}"
                )
            )
            self.stdout.write(
                "Check the admin: http://127.0.0.1:8000/admin/news/article/"
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR("✖ Database Save Test Failed!"))
            self.stderr.write(f"Error details: {str(e)}")
            import traceback

            self.stderr.write(traceback.format_exc())
