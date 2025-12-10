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



class SubdomainURLRoutingMiddleware:
    """
    Switch URLconf based on the requested domain/subdomain.
    Supports local testing via localhost or dev tunnels.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # strip port
        parts = host.split('.')

        # Default to main site
        urlconf = 'core.urls'

        # Local testing: uchumithrifts.localhost → storefront
        if host.endswith('localhost') or host.startswith('127.0.0.1'):
            if len(parts) == 2:  # e.g., uchumithrifts.localhost
                subdomain = parts[0]
                urlconf = 'core.storefront_urls'  # <-- update the variable
        else:
            # Production-style domain
            if host == 'bazaa.digital':
                urlconf = 'core.urls'
            elif host.endswith('.bazaa.digital'):
                urlconf = 'core.storefront_urls'

        request.urlconf = urlconf  # <-- only set here once
        return self.get_response(request)

