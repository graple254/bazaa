from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles=None, login_url='login'):
    """
    Restrict access to logged-in users with roles listed in allowed_roles.
    - allowed_roles: ['shop_manager', 'admin', ...]
    - If None: only requires authentication.
    """

    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            # User must be authenticated first
            if not request.user.is_authenticated:
                return redirect(login_url)

            # If no role restriction provided → allow any authenticated user
            if not allowed_roles:
                return view_func(request, *args, **kwargs)

            # Extract the user's role field from custom User model
            user_role = getattr(request.user, "role", None)

            if user_role is None:
                raise PermissionDenied("No role assigned.")

            # Role check
            if user_role not in allowed_roles:
                raise PermissionDenied("Insufficient permissions.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator



# Convenience decorator for shop managers only
def shop_manager_required(view_func=None, login_url='login'):
    """Shortcut to allow only users with role='shop_manager'."""
    
    if callable(view_func):
        return role_required(
            allowed_roles=['shop_manager'],
            login_url=login_url
        )(view_func)

    return role_required(
        allowed_roles=['shop_manager'],
        login_url=login_url
    )

