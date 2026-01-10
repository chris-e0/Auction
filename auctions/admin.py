from django.contrib import admin

from .models import Bid, Listing, User, Comment
# Register your models here.

class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "starting_bid", "creator", "created_at", "active")


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name")

class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "listing","comment", "commenter", "comment_time")

class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "amount", "bidder", "bid_time",)

admin.site.register(User, UserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Comment,CommentAdmin)