from django.contrib import admin
from .models import ProductCategory, Product, Inventory

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_created')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('category', 'blood_group', 'volume_ml', 'price')
    list_filter = ('category', 'blood_group')
    search_fields = ('blood_group',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_bank', 'product', 'quantity', 'expiry_date', 'date_created')
    list_filter = ('blood_bank', 'product__blood_group', 'expiry_date')
    search_fields = ('blood_bank__name', 'product__blood_group')
    list_editable = ('quantity',)
    ordering = ('expiry_date',)
