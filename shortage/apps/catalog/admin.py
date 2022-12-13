from django.contrib import admin
from shortage.apps.blog.admin import BlogPostAdmin
from .models import (
    Organization,
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


class InstructionAdmin(admin.ModelAdmin):
    pass


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
    list_display = ["organization"] + BlogPostAdmin.list_display
    fields = ["organization"] + BlogPostAdmin.fields


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(
    OrganizationRegistrationRequest, OrganizationRegistrationRequestAdmin
)
admin.site.register(OrganizationBlogPost, OrganizationBlogPostAdmin)
