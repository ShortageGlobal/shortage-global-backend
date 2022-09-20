from django.contrib import admin
from .models import Package, PackageItem, Cart, CartItem, CorporateDonation
from django.utils.html import format_html


class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "status",
        "owner",
        "full_name",
        "email",
        "phone_number",
        "delivery_company",
        "tracking_code",
        "status",
        "photo_preview",
        "created_at",
    ]
    fields = [
        "owner",
        "full_name",
        "email",
        "phone_number",
        "delivery_company",
        "tracking_code",
        "status",
        "photo_preview",
        "created_at",
        "note",
    ]
    readonly_fields = [
        "uuid",
        "owner",
        "full_name",
        "email",
        "phone_number",
        "delivery_company",
        "tracking_code",
        "photo_preview",
        "created_at",
    ]
    search_fields = ["full_name", "email"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ["-created_at"]

    def photo_preview(self, obj):
        if obj.photo:
            html = format_html('<img width=300 src="{}" />'.format(obj.photo.url))
        else:
            html = "No photo"
        return html

    photo_preview.short_description = "Photo preview"


class PackageItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "created_at", "package"]
    fields = ["package", "product", "quantity", "created_at"]
    readonly_fields = ["package", "product", "quantity", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


class CartAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "owner",
        "uuid",
    ]
    readonly_fields = [
        "uuid",
        "owner",
        "created_at",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ["-created_at"]


class CartItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "created_at", "cart"]
    fields = ["cart", "product", "quantity", "created_at"]
    readonly_fields = ["cart", "product", "quantity", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


class CorporateDonationAdmin(admin.ModelAdmin):
    list_display = [
        "company_name",
        "first_name",
        "last_name",
        "email",
        "city",
        "country",
        "estimated_value",
        "photo_preview",
        "created_at",
    ]
    fields = [
        "company_name",
        "department",
        "first_name",
        "last_name",
        "phone_number",
        "email",
        "address_line1",
        "address_line2",
        "city",
        "state_province_region",
        "zip",
        "country",
        "description",
        "quantity_description",
        "number_of_pallets",
        "estimated_value",
        "url",
        "photo_preview",
        "created_at",
    ]
    readonly_fields = [
        "created_at",
    ]
    search_fields = ["company_name", "first_name", "last_name"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ["-created_at"]

    def photo_preview(self, obj):
        if obj.photo:
            html = format_html('<img width=300 src="{}" />'.format(obj.photo.url))
        else:
            html = "No photo"
        return html

    photo_preview.short_description = "Photo preview"


admin.site.register(Package, PackageAdmin)
admin.site.register(PackageItem, PackageItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(CorporateDonation, CorporateDonationAdmin)
