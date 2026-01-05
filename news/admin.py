from django.contrib import admin
from .models import NewsPost

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "highlight", "is_published", "published_at")
    list_filter = ("highlight", "is_published", "published_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "summary", "body")
