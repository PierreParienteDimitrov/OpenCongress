from django.contrib import admin

from .models import Bill, Member, MemberVote, Seat, Vote


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["bioguide_id", "full_name", "party", "chamber", "state", "is_active"]
    list_filter = ["chamber", "party", "state", "is_active"]
    search_fields = ["bioguide_id", "full_name", "last_name"]
    ordering = ["last_name"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["seat_id", "chamber", "section", "row", "position", "member"]
    list_filter = ["chamber", "section"]
    search_fields = ["seat_id"]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ["bill_id", "display_number", "short_title", "congress", "sponsor"]
    list_filter = ["congress", "bill_type"]
    search_fields = ["bill_id", "title", "short_title"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["vote_id", "date", "chamber", "description", "result"]
    list_filter = ["chamber", "result", "congress"]
    search_fields = ["vote_id", "description"]
    date_hierarchy = "date"


@admin.register(MemberVote)
class MemberVoteAdmin(admin.ModelAdmin):
    list_display = ["vote", "member", "position"]
    list_filter = ["position"]
    search_fields = ["member__full_name", "vote__vote_id"]
