from django.contrib import admin
from shortage.apps.blog.models import BlogPost


class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "created_at",
        "is_published",
    ]
    search_fields = ["title"]
    fields = [
        "author",
        "title",
        "content",
        "is_published",
    ]
    readonly_fields = ["author"]
    list_filter = ["created_at", "is_published"]
    search_fields = ["author__email", "title"]

    # use current user as author
    def save_model(self, request, obj, form, change):
        if getattr(obj, "author", None) is None:
            obj.author = request.user
        return super().save_model(request, obj, form, change)


admin.site.register(BlogPost, BlogPostAdmin)
