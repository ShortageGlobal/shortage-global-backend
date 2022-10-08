from django.contrib import admin
from .models import (
    Organization,
    Product,
    Instruction,
    OnlineStore,
    OrganizationRegistrationRequest,
)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_verified",
        "is_draft",
        "owner",
        "created_at",
    ]
    search_fields = ["name"]


class InstructionAdmin(admin.ModelAdmin):
    pass


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "category",
        "price",
        "requested_amount",
        "top_priority",
        "is_deleted",
        "created_at",
    ]
    search_fields = ["name"]
    autocomplete_fields = ["organization"]


class OnlineStoreAdmin(admin.ModelAdmin):
    list_display = ["url", "product", "name", "created_at"]
    autocomplete_fields = ["product"]


class OrganizationRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "phone_number",
        "email",
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


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(OnlineStore, OnlineStoreAdmin)
admin.site.register(
    OrganizationRegistrationRequest, OrganizationRegistrationRequestAdmin
)
