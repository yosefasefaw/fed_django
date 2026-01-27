import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import FetchLog
from news.utils import is_in_fomc_critical_window, is_in_mock_critical_window

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
            FetchLog.objects.create(message=msg)
        else:
            self.stdout.write(f"SKIPPING: (Critical Window: {is_critical}) at {now.strftime('%H:%M:%S')}")
