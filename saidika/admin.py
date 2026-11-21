from django.contrib import admin

from .models import Order, OrderItem, Outfit, Payment, Product, Profile


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "in_stock")
    list_filter = ("category", "in_stock")
    search_fields = ("name",)


@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ("name", "body_type")
    filter_horizontal = ("products",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "status", "created")
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "amount", "status", "receipt", "created")
    list_filter = ("purpose", "status")


admin.site.register(Profile)
