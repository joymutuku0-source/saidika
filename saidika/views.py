from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Payment
from .serializers import ProductSerializer, PaymentSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all().order_by("-created")
    serializer_class = PaymentSerializer


@api_view(["GET"])
def home(request):
    return Response({
        "message": "Saidika API is live",
        "endpoints": ["/api/products/", "/api/payments/"],
    })

# Create your views here.
