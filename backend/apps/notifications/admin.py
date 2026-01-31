from django.contrib import admin

from .models import EmailLog, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "notification_type", "title", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["user__username", "title"]
    date_hierarchy = "created_at"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ["user", "subject", "template_name", "sent_at", "status"]
    list_filter = ["status", "template_name"]
    search_fields = ["user__username", "subject"]
