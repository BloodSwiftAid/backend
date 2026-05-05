from django.db import models
from core.model import BaseModel
from users.models import BloodBank

class ProductCategory(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(BaseModel):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    blood_group = models.CharField(max_length=10) # e.g. A+, O-
    volume_ml = models.DecimalField(max_digits=10, decimal_places=2, help_text="Volume in ml")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.blood_group} ({self.volume_ml}ml)"

class Inventory(BaseModel):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - {self.product} - {self.quantity}"
