from django.contrib import admin
from .models import Organization, Product, Instruction, OnlineStore, Package, PackageItem
from django.utils.html import format_html


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_draft', 'is_validated', 'is_deleted', 'created_at']
    search_fields = ['name']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'price', 'requested_amount', 'top_priority', 'created_at']
    search_fields = ['name']
    autocomplete_fields = ['organization']


class InstructionAdmin(admin.ModelAdmin):
    pass


class OnlineStoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'url', 'created_at']
    autocomplete_fields = ['product']


class PackageAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'email', 'tracking_code', 'status', 'created_at']
    fields = [
        'status',
        'full_name',
        'email',
        'phone_number',
        'delivery_company',
        'tracking_code',
        'note',
        'photo_preview',
        'created_at',
    ]
    readonly_fields = [
        'uuid',
        'full_name',
        'email',
        'phone_number',
        'delivery_company',
        'tracking_code',
        'note',
        'photo_preview',
        'created_at',
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def get_ordering(self, request):
        return super().get_ordering(request) or ['-created_at']

    def photo_preview(self, obj):
        if obj.photo:
            html = format_html('<img width=300 src="{}" />'.format(obj.photo.url))
        else:
            html = 'No photo'
        return html

    photo_preview.short_description = 'Photo preview'


class PackageItemAdmin(admin.ModelAdmin):
    list_display = ['package', 'product', 'quantity', 'created_at']
    fields = ['package', 'product', 'quantity', 'created_at']
    readonly_fields = ['package', 'product', 'quantity', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False    


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(OnlineStore, OnlineStoreAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(PackageItem, PackageItemAdmin)
