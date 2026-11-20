from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    

    def __str__(self):
        return self.name
    
class Payment(models.Model):
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    receipt = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    created = models.DateTimeField(auto_now_add=True)

    
