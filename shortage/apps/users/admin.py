from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ShortageUser, Profile


class ShortageUserAdmin(admin.ModelAdmin):
    exclude = ("password",)
    ordering = ("-date_joined",)
    list_display = ("email", "first_name", "last_name", "is_active", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    readonly_fields = ("email",)
    fieldsets = (
        (
            "Personal info",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
    )


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
    search_fields = ["user", "phone_number"]


admin.site.register(ShortageUser, ShortageUserAdmin)
admin.site.register(Profile, ProfileAdmin)
