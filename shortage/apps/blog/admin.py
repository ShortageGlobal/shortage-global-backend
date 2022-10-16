from django.contrib import admin
from shortage.apps.blog.models import BlogPost


class BlogPostAdmin(admin.ModelAdmin):
    class Media:
        js = ("js/tinyInject.js",)

    list_display = [
        "author",
        "title",
        "created_at",
        "is_published",
    ]
    search_fields = ["title"]
    fields = [
        "organization",
        "author",
        "title",
        "content",
        "is_published",
    ]
    autocomplete_fields = ["organization"]


admin.site.register(BlogPost, BlogPostAdmin)
