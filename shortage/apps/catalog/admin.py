from django.contrib import admin
from .models import Organization, Product, Instruction, OnlineStore


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
        "created_at",
    ]
    search_fields = ["name"]
    autocomplete_fields = ["organization"]


class OnlineStoreAdmin(admin.ModelAdmin):
    list_display = ["url", "product", "name", "created_at"]
    autocomplete_fields = ["product"]


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(OnlineStore, OnlineStoreAdmin)
