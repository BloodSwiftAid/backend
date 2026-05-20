from django.db import models
from core.model import BaseModel
from users.models import BloodBank

class BloodType(BaseModel):
    group = models.CharField(max_length=10, unique=True) # e.g. A+, O-
    is_active = models.BooleanField(default=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.group} (Base: ₦{self.base_price})"

class ProductCategory(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(BaseModel):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    blood_group = models.CharField(max_length=10) # e.g. A+, O-
    volume_ml = models.DecimalField(max_digits=10, decimal_places=2, help_text="Volume in ml")

    def __str__(self):
        return f"{self.blood_group} ({self.volume_ml}ml)"

class Inventory(BaseModel):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    blood_type = models.ForeignKey(BloodType, on_delete=models.CASCADE, related_name='inventory_items', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_items', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        bank = self.blood_bank.name if self.blood_bank else 'System'
        btype = self.blood_type.group if self.blood_type else 'Unknown'
        product = self.product.blood_group if self.product else '—'
        return f"{bank} - {btype} / {product} - qty:{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.product and self.blood_type:
            # Auto-resolve product from the blood type's group
            product = Product.objects.filter(blood_group=self.blood_type.group).first()
            if product:
                self.product = product
        super().save(*args, **kwargs)

class Donation(BaseModel):
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    )
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='donations')
    donor_name = models.CharField(max_length=255)
    donor_email = models.EmailField(blank=True, null=True)
    donor_phone = models.CharField(max_length=20, blank=True, null=True)
    donor_gender = models.CharField(max_length=10, choices=(('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')), blank=True, null=True)
    donor_age = models.IntegerField(blank=True, null=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    volume_ml = models.DecimalField(max_digits=10, decimal_places=2)
    hemoglobin_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Hemoglobin level in g/dL")
    genotype = models.CharField(max_length=10, null=True, blank=True, help_text="e.g. AA, AS, AC, SS")
    donation_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Donation {self.id} - {self.donor_name} ({self.blood_group})"
