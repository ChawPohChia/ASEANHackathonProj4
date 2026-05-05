from django.contrib import admin

from .models import SentimentAnalysis, XPost


class SentimentInline(admin.StackedInline):
    model = SentimentAnalysis
    extra = 0
    readonly_fields = ("classified_at",)


@admin.register(XPost)
class XPostAdmin(admin.ModelAdmin):
    list_display = ("post_id", "author_username", "post_created_at", "fetched_at")
    search_fields = ("post_id", "author_username", "text")
    inlines = [SentimentInline]


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ("post", "score", "model_name", "prompt_version", "classified_at")
    list_filter = ("prompt_version", "model_name")
