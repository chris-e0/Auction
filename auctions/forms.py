from django import forms
from .models import Listing, Bid, Comment

class ListingForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('', 'Select a category'),
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('home', 'Home & Garden'),
        ('toys', 'Toys & Hobbies'),
        ('books', 'Books & Media'),
        ('vehicles', 'Vehicles'),
        ('art', 'Art & Collectibles'),
        ('other', 'Other'),
        ('furniture', 'Furniture'),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']

