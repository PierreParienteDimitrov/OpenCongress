from django.contrib import admin

from .models import AISummary, NewsLink, TrendReport, WeeklySummary


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ["content_type", "content_id", "model_used", "created_at"]
    list_filter = ["content_type", "model_used"]
    search_fields = ["content_id"]


@admin.register(TrendReport)
class TrendReportAdmin(admin.ModelAdmin):
    list_display = ["report_type", "period_start", "period_end", "created_at"]
    list_filter = ["report_type"]
    date_hierarchy = "period_start"


@admin.register(NewsLink)
class NewsLinkAdmin(admin.ModelAdmin):
    list_display = ["title", "source", "published_at"]
    list_filter = ["source"]
    search_fields = ["title", "bill_id", "vote_id"]


@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    list_display = ["year", "week_number", "summary_type", "model_used", "created_at"]
    list_filter = ["summary_type", "year", "model_used"]
    search_fields = ["content"]
    ordering = ["-year", "-week_number", "summary_type"]
    readonly_fields = ["created_at", "tokens_used", "votes_included", "bills_included"]
