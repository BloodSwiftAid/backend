from django.contrib import admin
from .models import BloodType, ProductCategory, Product, Inventory, Donation

@admin.register(BloodType)
class BloodTypeAdmin(admin.ModelAdmin):
    list_display = ('group', 'base_price', 'is_active', 'date_created')
    list_editable = ('base_price', 'is_active')
    search_fields = ('group',)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('category', 'blood_group', 'volume_ml')
    list_filter = ('category', 'blood_group')
    search_fields = ('blood_group',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_bank', 'blood_type', 'quantity', 'price', 'expiry_date', 'date_created')
    list_filter = ('blood_bank', 'blood_type__group', 'expiry_date')
    search_fields = ('blood_bank__name', 'blood_type__group')
    list_editable = ('quantity',)
    ordering = ('expiry_date',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'blood_group', 'volume_ml', 'hemoglobin_level', 'genotype', 'blood_bank', 'donation_date')
    list_filter = ('blood_group', 'blood_bank', 'donation_date')
    search_fields = ('donor_name', 'donor_phone', 'donor_email')
    readonly_fields = ('donation_date',)
