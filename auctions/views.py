from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal
from django.contrib import messages

from .models import User, Listing, Bid, Comment, ListingView
from .forms import ListingForm


def index(request):
    listings = Listing.objects.filter(active=True)  
    return render(request, "auctions/index.html", {
        "listings": listings  
    })

@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user  # Set the creator to current user
            listing.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ListingForm()
    
    return render(request, "auctions/create_listing.html", {
        "form": form
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        first_name = request.POST["first_name"] 
        last_name = request.POST["last_name"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = first_name  
            user.last_name = last_name    
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def listing_page(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.user.is_authenticated:
        ListingView.objects.update_or_create(
        user=request.user,
        listing=listing
        )

    bids = listing.bids.all()

    order = request.GET.get("order", "newest")
    if order == "oldest":
        comments = listing.comments.order_by("comment_time")
    else:
        comments = listing.comments.order_by("-comment_time")

    
    if bids.exists():
        highest_bid = bids.order_by('-amount').first()
        current_price = highest_bid.amount
        last_bidder = highest_bid.bidder  
    else:
        current_price = listing.starting_bid
        last_bidder = None  

    if request.method == "POST":
        # -------- BIDDING --------
        if "bid_amount" in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to bid.")

            elif not listing.active:
                messages.error(request, "This auction is closed.")    

            elif request.user == listing.creator:
                messages.error(request, "You cannot bid on your own listing.")
            else:
                try:
                    bid_amount = Decimal(request.POST["bid_amount"])
                except:
                    messages.error(request, "Invalid bid amount.")
                else:
                    if bid_amount < listing.starting_bid:
                        messages.error(
                            request,
                            "Bid must be at least the starting bid."
                        )
                    elif bid_amount <= current_price:
                        messages.error(
                            request,
                            "Bid must be higher than the current bid."
                        )
                    else:
                        Bid.objects.create(
                            listing=listing,
                            bidder=request.user,
                            amount=bid_amount
                        )
                        listing.save()
                        messages.success(request, "Bid placed successfully.")
                        return HttpResponseRedirect(
                            reverse("listing", args=[listing.id])
                        )

        # -------- COMMENTS --------
        elif "comment_text" in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in to comment.")
            else:
                text = request.POST["comment_text"].strip()
                if text:
                    Comment.objects.create(
                        listing=listing,
                        commenter=request.user,
                        comment=text
                    )
                    listing.save()
                    return HttpResponseRedirect(
                        reverse("listing", args=[listing.id])
                    )
        elif "close_auction" in request.POST:
            if request.user != listing.creator:
                messages.error(request, "You are not allowed to close this auction.")
            else:
                listing.active = False
                highest_bid = listing.bids.order_by("-amount").first()
                if highest_bid:
                    listing.winner = highest_bid.bidder
                listing.save()
                messages.success(request, "Auction closed successfully.")
                return HttpResponseRedirect(reverse("listing", args=[listing.id]))
            
        elif "toggle_watchlist" in request.POST:
            if not request.user.is_authenticated:
                messages.error(request, "You must be logged in.")
            else:
                if listing in request.user.watchlist.all():
                    request.user.watchlist.remove(listing)
                    messages.success(request, "Removed from watchlist.")
                else:
                    request.user.watchlist.add(listing)
                    messages.success(request, "Added to watchlist.")

                return HttpResponseRedirect(
                    reverse("listing", args=[listing.id])
                )



    return render(request, "auctions/listing_page.html", {
        "listing": listing,
        "current_price": current_price,
        "last_bidder": last_bidder,
        "comments": comments
    })

@login_required
def watchlist(request):
    listings = request.user.watchlist.all().order_by('-active', '-last_updated')  # Active first, then by update time
    
    listings_with_updates = []
    for listing in listings:
        # Add current_price
        bids = listing.bids.all()
        if bids.exists():
            highest_bid = bids.order_by('-amount').first()
            listing.current_price = highest_bid.amount
            listing.last_bidder = highest_bid.bidder
        else:
            listing.current_price = listing.starting_bid
            listing.last_bidder = None
        
        # Check if there are updates since last view
        try:
            lv = ListingView.objects.get(user=request.user, listing=listing)
            has_updates = (
                Bid.objects.filter(listing=listing, bid_time__gt=lv.last_seen).exists() or
                Comment.objects.filter(listing=listing, comment_time__gt=lv.last_seen).exists()
            )
        except ListingView.DoesNotExist:
            has_updates = True
        
        listing.has_updates = has_updates
        listings_with_updates.append(listing)
    
    return render(request, "auctions/watchlist.html", {
        "listings": listings_with_updates
    })

def categories(request):
    categories = Listing.objects.filter(active=True).values_list('category', flat=True).distinct()
    categories = [cat for cat in categories if cat]
    
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_name):
    listings = Listing.objects.filter(active=True, category=category_name)
    
    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": listings
    })


@login_required
def my_listings(request):
    listings = Listing.objects.filter(creator=request.user).order_by('-active', '-last_updated')
    
    # Add notification flags and current price
    listings_with_updates = []
    for listing in listings:
        # Add current_price
        bids = listing.bids.all()
        if bids.exists():
            highest_bid = bids.order_by('-amount').first()
            listing.current_price = highest_bid.amount
            listing.last_bidder = highest_bid.bidder  
        else:
            listing.current_price = listing.starting_bid
            listing.last_bidder = None 
        
        # Check if there are updates since last view
        try:
            lv = ListingView.objects.get(user=request.user, listing=listing)
            has_updates = (
                Bid.objects.filter(listing=listing, bid_time__gt=lv.last_seen).exists() or
                Comment.objects.filter(listing=listing, comment_time__gt=lv.last_seen).exists()
            )
        except ListingView.DoesNotExist:
            has_updates = True  # Never seen = has updates
        
        listing.has_updates = has_updates
        listings_with_updates.append(listing)
    
    return render(request, "auctions/my_listings.html", {
        "listings": listings_with_updates
    })