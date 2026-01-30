import datetime
from django.utils import timezone

from core.constants import FOMC_CALENDAR


def is_in_fomc_critical_window(now=None):
    """
    Checks if the given time (defaults to now) is within
    24h before to 9h after an FOMC meeting.
    """
    if now is None:
        now = timezone.now()

    for meeting_date in FOMC_CALENDAR:
        # Ensure meeting_date is aware (assume UTC as per constants.py comment)
        if timezone.is_naive(meeting_date):
            aware_meeting = timezone.make_aware(meeting_date, datetime.timezone.utc)
        else:
            aware_meeting = meeting_date

        window_start = aware_meeting - datetime.timedelta(hours=24)
        window_end = aware_meeting + datetime.timedelta(hours=24)

        if window_start <= now <= window_end:
            return aware_meeting

    return None


def update_next_run_time(last_run_critical, last_run_daily, is_critical):
    """
    Calculates and saves the next scheduled run time to the DB.
    """
    from multi_agent_systems.models import SystemMetadata
    
    now = timezone.now()
    next_run = None
    
    if is_critical:
        # Critical Mode: Runs every 3 hours
        # If we just ran, next run is last_run + 3h. 
        # If we haven't run recently, it's effectively "now" (or immediately handled by loop)
        if last_run_critical:
            next_run = last_run_critical + datetime.timedelta(hours=3)
        else:
            next_run = now # Should run immediately
    else:
        # Standard Mode: Runs daily at 8 AM UTC
        today_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
        
        if now < today_8am:
            next_run = today_8am
        else:
            next_run = today_8am + datetime.timedelta(days=1)
            
    # Save to DB
    if next_run:
        SystemMetadata.objects.update_or_create(
            key="next_scheduled_run",
            defaults={"value": next_run.isoformat()}
        )
        print(f"   🔮 Next Scheduled Run: {next_run.strftime('%Y-%m-%d %H:%M UTC')}")
