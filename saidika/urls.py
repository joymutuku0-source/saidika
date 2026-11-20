from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("products", views.ProductViewSet)
router.register("payments", views.PaymentViewSet)

urlpatterns = [
    path("", views.home),
    path("api/", include(router.urls)),
]