from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass
    watchlist = models.ManyToManyField("Listing", blank=True, related_name="watchers")

class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_auctions")
    last_updated = models.DateTimeField(auto_now=True)

    def current_price(self):
        bids = self.bids.all()
        if bids.exists():
            return bids.order_by('-amount').first().amount
        else:
            return self.starting_bid
        
    def __str__(self):
        return f"{self.title} (ID: {self.id})"

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_bid")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    comment_time = models.DateTimeField(auto_now_add=True)

class ListingView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "listing")
