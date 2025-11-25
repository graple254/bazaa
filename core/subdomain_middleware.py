from django.utils.deprecation import MiddlewareMixin
from .models import Store

class SubdomainMiddleware(MiddlewareMixin):
    EXCLUDED_HOSTS = []

    def process_request(self, request):
        host = request.get_host().split(':')[0]  # remove port
        parts = host.split('.')

        # Determine subdomain
        subdomain = None
        if len(parts) >= 3:
            subdomain = parts[0]
        elif len(parts) == 2 and parts[1] in ["localhost", "devtunnels.ms"]:
            subdomain = parts[0]

        # Skip excluded hosts
        if not subdomain or subdomain in self.EXCLUDED_HOSTS:
            request.subdomain_store = None
            return

        # Try fetching store
        try:
            request.subdomain_store = Store.objects.get(subdomain=subdomain)
        except Store.DoesNotExist:
            request.subdomain_store = None
