from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ShortageUser, Profile


class ShortageUserAdmin(admin.ModelAdmin):
    exclude = ("password",)
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_superuser",)
    readonly_fields = ("email",)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number")
    search_fields = ["user", "phone_number"]


admin.site.register(ShortageUser, ShortageUserAdmin)
admin.site.register(Profile, ProfileAdmin)
