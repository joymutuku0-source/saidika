from django.conf import settings
from django.db import models

BODY_TYPES = [
    ("hourglass", "Hourglass"),
    ("pear", "Pear"),
    ("rectangle", "Rectangle"),
    ("apple", "Apple"),
    ("inverted", "Inverted Triangle"),
]

SIZES = [("XS", "XS"), ("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"), ("XXL", "XXL")]

CATEGORIES = [
    ("tops", "Tops"),
    ("bottoms", "Bottoms"),
    ("outerwear", "Outerwear"),
    ("footwear", "Footwear"),
]


class Profile(models.Model):
    """Extra info for each registered user: phone, size, body type, fee status."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=15, blank=True)
    size = models.CharField(max_length=3, choices=SIZES, blank=True)
    body_type = models.CharField(max_length=20, choices=BODY_TYPES, blank=True)
    style = models.CharField(max_length=30, blank=True)
    registration_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=40, blank=True)
    image = models.CharField(
        max_length=200, default="saidika/images/tops.jpg",
        help_text="Path inside the static folder, e.g. saidika/images/tops.jpg",
    )
    in_stock = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Outfit(models.Model):
    """A ready-made capsule for one body type."""
    name = models.CharField(max_length=120)
    body_type = models.CharField(max_length=20, choices=BODY_TYPES)
    tagline = models.CharField(max_length=200, blank=True)
    tips = models.TextField(blank=True, help_text="Styling advice shown with the capsule")
    products = models.ManyToManyField(Product, related_name="outfits")

    def __str__(self):
        return f"{self.name} ({self.get_body_type_display()})"

    @property
    def total(self):
        return sum(p.price for p in self.products.all())


class Order(models.Model):
    STATUS = [("PENDING", "Pending"), ("PAID", "Paid"), ("FAILED", "Failed")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="PENDING")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.price * self.quantity


class Payment(models.Model):
    PURPOSE = [("REGISTRATION", "Registration fee"), ("ORDER", "Order")]
    STATUS = [("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    purpose = models.CharField(max_length=15, choices=PURPOSE)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    receipt = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="PENDING")
    note = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.purpose} KES {self.amount} - {self.status}"
