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
        # Simple timezone awareness
        if timezone.is_naive(meeting_date):
            aware_meeting = timezone.make_aware(meeting_date)
        else:
            aware_meeting = meeting_date

        window_start = aware_meeting - datetime.timedelta(hours=24)
        window_end = aware_meeting + datetime.timedelta(hours=9)

        if window_start <= now <= window_end:
            return True

    return False


def is_in_mock_critical_window(now=None):
    """
    Mock logic: Returns True if the current minute is a multiple of 5
    (e.g., 00, 05, 10, 15...).
    """
    if now is None:
        now = timezone.now()

    return now.minute % 5 == 0
