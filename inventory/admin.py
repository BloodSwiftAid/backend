from django.contrib import admin
from django.utils.html import format_html
from .models import BloodType, ProductCategory, Product, Inventory, Donation


# ─────────────────────────────────────────────
#  BLOOD TYPE
# ─────────────────────────────────────────────
@admin.register(BloodType)
class BloodTypeAdmin(admin.ModelAdmin):
    list_display = ('group', 'base_price', 'is_active', 'created_by', 'date_created')
    list_editable = ('base_price', 'is_active')
    search_fields = ('group',)
    ordering = ('group',)
    readonly_fields = ('created_by', 'date_created')

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  PRODUCT CATEGORY
# ─────────────────────────────────────────────
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'date_created')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_by', 'date_created')

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  PRODUCT
# ─────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('blood_group', 'category', 'volume_ml', 'created_by', 'date_created')
    list_filter = ('category', 'blood_group')
    search_fields = ('blood_group', 'category__name')
    ordering = ('blood_group',)
    readonly_fields = ('created_by', 'date_created')

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  INVENTORY
# ─────────────────────────────────────────────
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'blood_bank', 'blood_type', 'product',
        'quantity', 'price', 'expiry_date',
        'created_by', 'date_created',
    )
    list_filter = ('blood_bank', 'blood_type__group', 'expiry_date')
    search_fields = ('blood_bank__name', 'blood_type__group', 'product__blood_group')
    list_editable = ('quantity', 'price')
    ordering = ('expiry_date',)
    raw_id_fields = ('blood_bank', 'blood_type', 'product')
    readonly_fields = ('created_by', 'date_created')

    fieldsets = (
        ('Facility & Product', {
            'fields': ('blood_bank', 'blood_type', 'product'),
        }),
        ('Stock', {
            'fields': ('quantity', 'price', 'expiry_date'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  DONATION
# ─────────────────────────────────────────────
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'donor_name', 'blood_group', 'genotype', 'volume_ml',
        'hemoglobin_level', 'blood_bank', 'created_by', 'donation_date',
    )
    list_filter = ('blood_group', 'genotype', 'donor_gender', 'blood_bank', 'donation_date')
    search_fields = ('donor_name', 'donor_phone', 'donor_email', 'blood_bank__name')
    ordering = ('-donation_date',)
    readonly_fields = ('donation_date', 'created_by', 'date_created')

    fieldsets = (
        ('Donor Identity', {
            'fields': ('donor_name', 'donor_email', 'donor_phone', 'donor_gender', 'donor_age'),
        }),
        ('Clinical', {
            'fields': ('blood_group', 'genotype', 'volume_ml', 'hemoglobin_level'),
        }),
        ('Assignment', {
            'fields': ('blood_bank', 'donation_date', 'notes'),
        }),
        ('Audit', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
