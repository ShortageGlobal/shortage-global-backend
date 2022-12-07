from django.contrib import admin


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "is_draft", "is_deleted"]
    fields = [
        "author",
        "title",
        "slug",
        "image",
        "content",
        "meta_description",
        "created_at",
        "updated_at",
        "is_draft",
        "is_deleted",
    ]
    readonly_fields = [
        "author",
        "created_at",
        "updated_at",
    ]
    list_filter = ["created_at", "is_draft", "is_deleted"]
    search_fields = ["author__email", "title"]
    ordering = ["-created_at"]

    # use current user as author
    def save_model(self, request, obj, form, change):
        if getattr(obj, "author", None) is None:
            obj.author = request.user
        return super().save_model(request, obj, form, change)
