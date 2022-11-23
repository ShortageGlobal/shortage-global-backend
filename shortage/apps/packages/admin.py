from django.contrib import admin
from .models import Package, PackageItem, Cart, CartItem, CorporateDonation
from django.utils.html import format_html


class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "status",
        "type",
        "owner",
        "full_name",
        "email",
        "need_tax_deduction",
        "delivery_company",
        "tracking_code",
    ]
    fields = [
        "type",
        "owner",
        "need_tax_deduction",
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
        "delivery_company",
        "tracking_code",
        "photo_preview",
        "created_at",
        "note",
        "checkout_url",
        "status",
        "tax_deduction_receipt",
    ]
    readonly_fields = [
        "type",
        "owner",
        "need_tax_deduction",
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
        "delivery_company",
        "tracking_code",
        "photo_preview",
        "created_at",
        "note",
        "checkout_url",
    ]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "delivery_company",
        "tracking_code",
    ]
    list_filter = ["type", "status", "created_at", "need_tax_deduction"]

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
    readonly_fields = ["created_at"]
    search_fields = ["package__pk", "product__name"]
    list_filter = ["created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CartAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "owner",
        "full_name",
        "email",
        "phone_number",
        "need_tax_deduction",
        "agreed_to_terms_of_use",
        "uuid",
    ]
    readonly_fields = ["created_at", "updated_at", "agreed_to_terms_of_use"]
    search_fields = [
        "email",
        "first_name",
        "last_name",
        "phone_number",
    ]
    list_filter = ["created_at", "need_tax_deduction", "agreed_to_terms_of_use"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ["-created_at"]


class CartItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "created_at", "cart"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["cart__pk", "product__name"]
    list_filter = ["created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
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
        "photo_preview",
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
