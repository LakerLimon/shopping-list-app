from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import EmailTokenObtainPairView, MeAPIView, RegisterAPIView
from shopping.views import (
    AcceptInvitationAPIView,
    HistoryAPIView,
    NotificationListAPIView,
    ProductBuyAPIView,
    ProductDetailAPIView,
    ProductListCreateAPIView,
    ShoppingListViewSet,
)

router = DefaultRouter()
router.register(r"lists", ShoppingListViewSet, basename="lists")

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
    path("invite/<uuid:code>/", TemplateView.as_view(template_name="index.html"), name="invite-page"),
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("api/auth/login/", EmailTokenObtainPairView.as_view(), name="auth-login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("api/lists/<int:list_id>/products/", ProductListCreateAPIView.as_view(), name="list-products"),
    path("api/lists/<int:list_id>/history/", HistoryAPIView.as_view(), name="list-history"),
    path("api/products/<int:product_id>/", ProductDetailAPIView.as_view(), name="product-detail"),
    path("api/products/<int:product_id>/buy/", ProductBuyAPIView.as_view(), name="product-buy"),
    path("api/invitations/<uuid:code>/accept/", AcceptInvitationAPIView.as_view(), name="invitation-accept"),
    path("api/notifications/", NotificationListAPIView.as_view(), name="notifications"),
    path("api/", include(router.urls)),
]
