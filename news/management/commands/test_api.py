from django.core.management.base import BaseCommand
from news.services import retrieve_articles
import json
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Quickly test the Event Registry API connection"

    def handle(self, *args, **options):
        self.stdout.write("Connecting to Event Registry API...")

        try:
            # We fetch just 2 articles as a sample
            articles = retrieve_articles(
                date_end=timezone.now(),
                date_start=timezone.now() - timedelta(hours=2),
                articles_count=2,
            )

            if articles:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Success! Retrieved {len(articles)} articles."
                    )
                )

                # Show the first one as a sample
                sample = articles[0]
                self.stdout.write(
                    self.style.MIGRATE_HEADING("\n--- Sample Article Data Model ---")
                )
                self.stdout.write(json.dumps(sample, indent=4))
                self.stdout.write(
                    self.style.MIGRATE_HEADING("--- End of Data Model ---\n")
                )

                self.stdout.write(
                    self.style.MIGRATE_LABEL("API Setup is 100% correct.")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Connected, but no articles were found. Check your date filters!"
                    )
                )

        except Exception as e:
            self.stderr.write(self.style.ERROR("✖ API Call Failed!"))
            self.stderr.write(f"Error details: {str(e)}")
