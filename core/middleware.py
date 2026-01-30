import zoneinfo
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Activate Europe/Paris timezone for the duration of the request
        # This affects template rendering and forms
        tzname = 'Europe/Paris'
        timezone.activate(zoneinfo.ZoneInfo(tzname))
        
        return self.get_response(request)
