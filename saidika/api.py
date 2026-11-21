"""Django REST Framework API for Saidika."""
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from . import mpesa
from .models import Outfit, Payment, Product


class ProductSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


class OutfitSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    body_type_label = serializers.CharField(source="get_body_type_display", read_only=True)

    class Meta:
        model = Outfit
        fields = ["id", "name", "body_type", "body_type_label", "tagline", "tips", "total", "products"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "purpose", "phone", "amount", "status", "receipt", "created"]
        read_only_fields = fields


class ReadOnlyOrStaff(permissions.BasePermission):
    """Anyone can read the catalogue; only staff can change it."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ReadOnlyOrStaff]


class OutfitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Outfit.objects.prefetch_related("products")
    serializer_class = OutfitSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Each user sees only their own payments (staff see all)."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Payment.objects.all()
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def api_root_info(request):
    return Response({
        "app": "Saidika - The Wardrobe Capsule API",
        "endpoints": {
            "products": "/api/products/",
            "outfits": "/api/outfits/",
            "payments (login required)": "/api/payments/",
            "daraja callback (POST, used by Safaricom)": "/api/mpesa/callback/",
        },
        "mpesa_mode": "simulation" if mpesa.simulation_mode() else "daraja " + mpesa.settings.MPESA_ENV,
    })


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def mpesa_callback(request):
    """Safaricom posts the STK Push result here."""
    try:
        mpesa.handle_callback(request.data)
    except (KeyError, TypeError):
        pass
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})
