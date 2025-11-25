from django.urls import path
from .views import *

urlpatterns = [
    path('index/', index_view, name='index'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('verify/', verify_view, name='verify'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', shop_manager_dashboard_view, name='dashboard'),
    path('product-management/', product_management_view, name='product_management'),
    path('create-store-profile/', create_store_profile, name='create_store_profile'),

    # HTMX endpoints
    path('dashboard/htmx/create-announcement/', create_announcement_htmx, name='create_announcement_htmx'),
    path('dashboard/htmx/edit-announcement/', edit_announcement_htmx, name='edit_announcement_htmx'),
    path('dashboard/htmx/toggle-announcement/', toggle_announcement_htmx, name='toggle_announcement_htmx'),
    path('dashboard/htmx/update-store/', update_store_htmx, name='update_store_htmx'),

    # --------------------------------------------------
    # STORE FRONT — MUST BE LAST!
    # --------------------------------------------------
    path('', storefront_view, name='storefront'),
]
