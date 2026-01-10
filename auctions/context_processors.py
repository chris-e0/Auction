from .models import ListingView, Bid, Comment

def notification_counts(request):
    if not request.user.is_authenticated:
        return {}

    watchlist_notifications = 0
    my_listings_notifications = 0

    for listing in request.user.watchlist.all():
        try:
            lv = ListingView.objects.get(
                user=request.user,
                listing=listing
            )
            # Check if there are new bids or comments since last visit
            new_bids = Bid.objects.filter(
                listing=listing,
                bid_time__gt=lv.last_seen
            ).exists()
            
            new_comments = Comment.objects.filter(
                listing=listing,
                comment_time__gt=lv.last_seen
            ).exists()
            
            if new_bids or new_comments:
                watchlist_notifications += 1
                
        except ListingView.DoesNotExist:
            # Never seen before → count as new
            watchlist_notifications += 1

    for listing in request.user.listings.all():  # listings YOU created
        try:
            lv = ListingView.objects.get(
                user=request.user,
                listing=listing
            )
            new_bids = Bid.objects.filter(
                listing=listing,
                bid_time__gt=lv.last_seen
            ).exists()
            
            new_comments = Comment.objects.filter(
                listing=listing,
                comment_time__gt=lv.last_seen
            ).exists()
            
            if new_bids or new_comments:
                my_listings_notifications += 1
                
        except ListingView.DoesNotExist:
            my_listings_notifications += 1

    return {
        "watchlist_notifications": watchlist_notifications,
        "my_listings_notifications": my_listings_notifications,
    }