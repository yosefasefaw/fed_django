from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import FetchLog
from news.utils import is_in_mock_critical_window
from news.services import retrieve_articles, save_articles


class Command(BaseCommand):
    help = "Test command using shared utility logic"

    def handle(self, *args, **options):
        now = timezone.now()

        # Call the MOCK utility function for testing!
        is_critical = is_in_mock_critical_window(now)

        should_run = False
        reason = ""

        if is_critical:
            # During mock "critical" window, we run every time we are called
            should_run = True
            reason = "Inside MOCK critical minute (5-min interval)"
        else:
            # Outside critical window: Only run if it's an even minute (for testing)
            if now.minute % 2 == 0:
                should_run = True
                reason = "Normal test interval (Even minute)"

        if should_run:
            msg = f"RUNNING: {reason} at {now.strftime('%H:%M:%S')}"
            self.stdout.write(self.style.SUCCESS(msg))
            
            # Fetch and Save News
            try:
                date_start = now - timedelta(hours=1)
                articles = retrieve_articles(date_start=date_start, date_end=now, articles_count=5)
                new_saved, updated = save_articles(articles)
                
                log_msg = f"{msg} | Fetched: {len(articles)}, New: {new_saved}, Updated: {updated}"
                FetchLog.objects.create(message=log_msg)
                self.stdout.write(self.style.MIGRATE_LABEL(f"   ∟ Data Sync Complete: {new_saved} new, {updated} updated."))
            except Exception as e:
                error_msg = f"FAILED Fetch at {now.strftime('%H:%M:%S')}: {str(e)}"
                self.stdout.write(self.style.ERROR(f"   ∟ {error_msg}"))
                FetchLog.objects.create(message=error_msg)
        else:
            self.stdout.write(
                f"SKIPPING: (Critical Window: {is_critical}) at {now.strftime('%H:%M:%S')}"
            )
