from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter()
router.register("products", api.ProductViewSet)
router.register("outfits", api.OutfitViewSet, basename="outfit")
router.register("payments", api.PaymentViewSet, basename="payment")

urlpatterns = [
    # public
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="saidika/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # registration payment
    path("activate/", views.activate, name="activate"),
    path("payment/<int:pk>/", views.payment_status, name="payment_status"),
    path("payment/<int:pk>/status/", views.payment_status_json, name="payment_status_json"),

    # members
    path("dashboard/", views.dashboard, name="dashboard"),
    path("curate/", views.curate, name="curate"),
    path("capsule/", views.capsule, name="capsule"),
    path("closet/", views.closet, name="closet"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/add-outfit/<int:pk>/", views.cart_add_outfit, name="cart_add_outfit"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),

    # REST API
    path("api/", api.api_root_info, name="api_info"),
    path("api/mpesa/callback/", api.mpesa_callback, name="mpesa_callback"),
    path("api/", include(router.urls)),
]
