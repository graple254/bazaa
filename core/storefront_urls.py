from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --------------------------------------------------
    # STORE FRONT — MUST BE LAST!
    # --------------------------------------------------
    path('', storefront_view, name='storefront'),
    path('product/<int:product_id>/', storefront_product_detail_view, name='product_detail'),
    path('like-product/<int:product_id>/', like_product_view, name='like_product'),
    path('add-comment/<int:product_id>/', add_comment_view, name='add_comment'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)