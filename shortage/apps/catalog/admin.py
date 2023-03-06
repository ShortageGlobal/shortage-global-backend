from django.contrib import admin
from shortage.apps.blog.admin import BlogPostAdmin
from .models import (
    Organization,
    ExternalOrganization,
    Product,
    Instruction,
    OrganizationRegistrationRequest,
    OrganizationBlogPost,
)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_verified",
        "is_draft",
        "promote",
        "owner",
        "created_at",
    ]
    search_fields = ["name"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "owner",
                    "name",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_verified",
                    "is_draft",
                    "is_deleted",
                    "promote",
                )
            },
        ),
        (
            "Nonprofit Page",
            {
                "classes": ("collapse",),
                "fields": (
                    "slug",
                    "deadline",
                    "url",
                    "logo",
                    "banner",
                    "description",
                    "requested_goods",
                    "mission_description",
                    "meta_description",
                ),
            },
        ),
        (
            "Tax Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "ein_number",
                    "address_line1",
                    "address_line2",
                    "city",
                    "state_province_region",
                    "zip",
                    "country",
                    "representative_first_name",
                    "representative_last_name",
                    "representative_email",
                    "representative_phone_number",
                    "representative_signature",
                    "tax_deduction_receipt_preamble",
                    "tax_deduction_receipt_legal_information",
                ),
            },
        ),
        (
            "Created at / Updated at",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    readonly_fields = [
        "created_at",
        "updated_at",
    ]


class ExternalOrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "created_at",
        "url",
        "position",
    ]
    search_fields = ["name"]


class InstructionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organization",
    ]


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organization",
        "category",
        "price",
        "top_priority",
    ]
    search_fields = ["name", "organization__name"]
    autocomplete_fields = ["organization"]
    list_filter = [
        "organization",
        "top_priority",
        "category",
        "created_at",
        "is_deleted",
    ]


class OrganizationRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "full_name",
        "phone_number",
        "organization_name",
        "ein_number",
        "created_at",
    ]
    fields = [
        "first_name",
        "last_name",
        "phone_number",
        "email",
        "organization_name",
        "ein_number",
        "url",
        "created_at",
    ]
    readonly_fields = [
        "created_at",
    ]
    search_fields = ["organization_name", "first_name", "last_name"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ["-created_at"]


class OrganizationBlogPostAdmin(BlogPostAdmin):
    list_display = (
        ["title", "organization"]
        + [x for x in BlogPostAdmin.list_display if x != "title"]
        + ["promote"]
    )
    fields = ["organization"] + BlogPostAdmin.fields + ["promote"]


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(ExternalOrganization, ExternalOrganizationAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(
    OrganizationRegistrationRequest, OrganizationRegistrationRequestAdmin
)
admin.site.register(OrganizationBlogPost, OrganizationBlogPostAdmin)
