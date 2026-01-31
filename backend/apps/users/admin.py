from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BillTrack, User, UserFollow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "state", "is_active", "date_joined"]
    list_filter = ["is_active", "is_staff", "state"]
    search_fields = ["username", "email"]
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "CongressTrack",
            {
                "fields": (
                    "address",
                    "state",
                    "congressional_district",
                    "email_notifications",
                    "push_notifications",
                )
            },
        ),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ["user", "bioguide_id", "created_at"]
    search_fields = ["user__username", "bioguide_id"]


@admin.register(BillTrack)
class BillTrackAdmin(admin.ModelAdmin):
    list_display = ["user", "bill_id", "created_at"]
    search_fields = ["user__username", "bill_id"]
