import requests
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.core.cache import cache
from .models import Visitor

class VisitorTrackingMiddleware(MiddlewareMixin):
    TIMEOUT = 60  # seconds to ignore repeated hits to same page

    def process_request(self, request):
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        ip_address = self.get_client_ip(request)
        session_key = request.session.session_key
        path = request.path
        method = request.method
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        cache_key = f"visitor:{session_key}:{path}"
        if cache.get(cache_key):
            return  # skip logging repeated hits within TIMEOUT

        location = self.get_location(ip_address)

        Visitor.objects.create(
            ip_address=ip_address,
            session_key=session_key,
            user_agent=user_agent,
            url_path=path,
            method=method,
            referrer=referrer,
            location=location,
            visit_date=now()
        )

        cache.set(cache_key, True, timeout=self.TIMEOUT)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def get_location(self, ip_address):
        try:
            cache_key = f"ip-location-{ip_address}"
            location = cache.get(cache_key)
            if location:
                return location

            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
            data = response.json()
            if data.get('status') != 'success':
                return 'Unknown'

            location = f"{data.get('city')}, {data.get('country')}"
            cache.set(cache_key, location, timeout=86400)  # cache for 24h
            return location
        except requests.RequestException:
            return 'Unknown'
