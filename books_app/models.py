from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from urllib.parse import quote

# --- Helper Model: Profile of the WhatsApp Requester ---
class RequesterProfile(models.Model):
    """
    Stores the details of a user who can request a book. 
    Crucial for identifying who to send the book to.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, null=True, help_text="Optional profile picture."
    )
    whatsapp_name = models.CharField(
        max_length=150, 
        help_text="The name the user uses in the WhatsApp group."
    )
    whatsapp_number = models.CharField(
        max_length=20, 
        unique=True, # Each number should be unique
        help_text="Required. Full phone number including country code, e.g., +255712345678."
    )
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.whatsapp_name
    
    class Meta:
        verbose_name = "Group Requester"
        verbose_name_plural = "Group Requesters"


# --- Core Model: Book Catalog ---
class BookAvailable(models.Model):
    """
    The main catalog of ebooks available for request. 
    This is likely the model you were working on.
    """
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    
    # Stores the actual file (PDF, EPUB, etc.) on the server.
    book_file = models.FileField(upload_to='books/files/') 
    
    # Stores the cover image file.
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True) 

    published_date = models.DateField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
    
    class Meta:
        verbose_name = "Available Book"
        verbose_name_plural = "Available Books"


# --- Transactional Model: The Request/Order ---
class BookRequest(models.Model):
    """
    A record of a user's request for a specific book.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('FULFILLED', 'Fulfilled (Sent to User)'),
        ('REJECTED', 'Rejected (e.g., Book Not Found)'),
        ('CONTACT', 'Contact Required (Issue with Request)')
    )
    
    requester = models.ForeignKey(RequesterProfile, on_delete=models.CASCADE)
    # Link to an existing book if it's in the catalog, otherwise it's a new request.
    book_requested = models.ForeignKey(BookAvailable, on_delete=models.SET_NULL, null=True, blank=True)

    # Fields for when the book is NOT in the catalog yet.
    book_title = models.CharField(max_length=200, help_text="Title of the requested book.")
    book_author = models.CharField(max_length=100, blank=True, help_text="Author of the requested book.")
    
    # The status of the request
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )

    
    request_date = models.DateTimeField(auto_now_add=True)
    fulfillment_date = models.DateTimeField(null=True, blank=True)
    
    # Notes for the admin (you) to track issues or confirmation details.
    admin_notes = models.TextField(blank=True, help_text="Notes on fulfillment, e.g., 'Sent via WhatsApp on 2025-10-23'.")

    def __str__(self):
        return f"Request by {self.requester.whatsapp_name} for {self.book_title}"

    def get_whatsapp_link(self):
        """Generates a WhatsApp link for the admin to contact the user quickly."""
        number = self.requester.whatsapp_number
        if not number:
            return mark_safe('<span style="color: red;">Number Missing</span>')

        # Generate a message to pre-fill the chat
        message = f"Hello {self.requester.whatsapp_name}, regarding your request for the book: '{self.book_title}'."
        
        # Use WhatsApp API link structure
        link = f"https://wa.me/{number}?text={quote(message)}"
        
        return mark_safe(f'<a href="{link}" target="_blank" style="color: green; font-weight: bold;">Open WhatsApp Chat</a>')
    
    get_whatsapp_link.allow_tags = True
    get_whatsapp_link.short_description = 'WhatsApp'

    class Meta:
        ordering = ['request_date']
        verbose_name = "Book Request/Order"
        verbose_name_plural = "Book Requests/Orders"
