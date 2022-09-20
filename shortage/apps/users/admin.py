from django.contrib import admin

from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["phone_number"]
    search_fields = ["phone_number"]


admin.site.register(Profile, ProfileAdmin)
