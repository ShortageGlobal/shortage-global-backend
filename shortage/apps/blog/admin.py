from django.contrib import admin
from shortage.apps.blog.models import BlogPost


class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "author",
        "title",
        "created_at",
        "is_published",
    ]
    search_fields = ["title"]
    fields = [
        "owner",
        "author",
        "title",
        "content",
        "is_published",
    ]
    autocomplete_fields = ["owner"]


admin.site.register(BlogPost, BlogPostAdmin)
