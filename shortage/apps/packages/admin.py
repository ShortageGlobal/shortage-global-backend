from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from .models import (
    Package,
    PackageBlogPost,
    PackageItem,
    PackageStatusLogEntry,
    Cart,
    CartItem,
    CorporateDonation,
)


class PackageBlogPostAdmin(admin.TabularInline):
    model = PackageBlogPost


class PackageAdmin(admin.ModelAdmin):
    change_form_template = "package_change_form.html"

    list_display = [
        "created_at",
        "organization",
        "campaign",
        "status",
        "type",
        "owner",
        "full_name",
        "email",
        "need_tax_deduction",
        "delivery_company",
        "tracking_code",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "organization",
                    "campaign",
                    "type",
                    "status",
                    "need_tax_deduction",
                    "tax_deduction_receipt",
                    "created_at",
                )
            },
        ),
        (
            "Donor",
            {
                "fields": (
                    "owner",
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                ),
            },
        ),
        (
            "Address",
            {
                "classes": ("collapse",),
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state_province_region",
                    "zip",
                    "country",
                ),
            },
        ),
        (
            "Tracking Details",
            {
                "classes": ("collapse",),
                "fields": (
                    "delivery_company",
                    "tracking_code",
                ),
            },
        ),
        (
            "Feedback",
            {
                "classes": ("collapse",),
                "fields": (
                    "note",
                    "photo_preview",
                    # "blog_posts",
                ),
            },
        ),
        (
            "Advanced",
            {
                "classes": ("collapse",),
                "fields": ("checkout_url", "shopify_order_id"),
            },
        ),
    )
    inlines = (PackageBlogPostAdmin,)

    readonly_fields = [
        "organization",
        "campaign",
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
        "shopify_order_id",
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
    ordering = ["-created_at"]

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

    def response_change(self, request, obj):
        if "_generate-tax-deduction-receipt" in request.POST:
            obj.generate_tax_receipt(force=True, save=True)
            self.message_user(
                request, "The tax deduction receipt was generated successfully."
            )
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


class PackageItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "price", "created_at", "package"]
    readonly_fields = ["created_at"]
    search_fields = ["package__pk", "product__name"]
    list_filter = ["created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PackageStatusLogEntryAdmin(admin.ModelAdmin):
    list_display = ["package", "status", "created_at"]
    # readonly_fields = ["package", "status", "created_at"]
    search_fields = ["package__pk"]
    list_filter = ["status", "created_at"]
    ordering = ["-created_at"]

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
    list_display = ["product", "campaign", "quantity", "created_at", "cart"]
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
admin.site.register(PackageStatusLogEntry, PackageStatusLogEntryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(CorporateDonation, CorporateDonationAdmin)
