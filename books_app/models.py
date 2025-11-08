from django.db import models
from django.utils.safestring import mark_safe # This is needed for rendering HTML in templates
from django.contrib.auth.models import User
from urllib.parse import quote
import os
import requests
from django.core.files.base import ContentFile
import io

try:
    import fitz # PyMuPDF
except ImportError:
    fitz = None # Define fitz as None if the import fails

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
        null=True, blank=True, # Allow number to be optional initially
        help_text="Optional. Full phone number including country code, e.g., +255712345678."
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
    
    # --- Tracking Fields ---
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times the book detail page has been viewed.")
    download_count = models.PositiveIntegerField(default=0, help_text="Number of times the book has been downloaded.")

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_pdf(self):
        """Checks if the book_file is a PDF for preview purposes."""
        if self.book_file and self.book_file.name:
            return self.book_file.name.lower().endswith('.pdf')
        return False

    def fetch_cover_from_google_books(self):
        """
        Searches the Google Books API for a cover image. It prioritizes results
        where the author matches the one provided.
        """
        if not self.title:
            return False # Cannot search without a title

        # Prepare the user-provided author name for comparison (lowercase, simple)
        user_author_normalized = self.author.lower().strip()

        search_term = f"{self.title} {self.author}"
        api_url = f"https://www.googleapis.com/books/v1/volumes?q={quote(search_term)}"

        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('totalItems', 0) > 0:
                # Iterate through the first few results to find a better match
                for item in data.get('items', []):
                    book_info = item.get('volumeInfo', {})
                    authors_from_api = book_info.get('authors', [])

                    # Check if any author from the API matches the user's input
                    author_match_found = False
                    for api_author in authors_from_api:
                        if user_author_normalized in api_author.lower():
                            author_match_found = True
                            break # Found a matching author, no need to check others for this book
                    
                    # If we found a matching author, this is likely the correct book.
                    if author_match_found:
                        image_links = book_info.get('imageLinks')
                        if image_links:
                            image_url = image_links.get('thumbnail') or image_links.get('smallThumbnail')
                            if image_url:
                                img_response = requests.get(image_url, timeout=10)
                                img_response.raise_for_status()
                                file_name = f"{self.title.replace(' ', '_')}_cover.jpg"
                                self.cover_image.save(file_name, ContentFile(img_response.content), save=False)
                                return True # Success, exit the function

        except requests.exceptions.RequestException:
            # Silently fail if there's a network issue or the API call fails
            pass
        return False # Indicate failure

    def generate_cover_from_pdf(self):
        """
        Generates a cover image from the first page of the book's PDF file.
        This is used as a fallback if Google Books API fails.
        Requires PyMuPDF (fitz) to be installed.
        """
        if not fitz or not self.book_file or not self.book_file.name.lower().endswith('.pdf'):
            return False

        try:
            # Open the PDF file from storage
            with self.book_file.open('rb') as file_stream:
                pdf_document = fitz.open(stream=file_stream.read(), filetype="pdf")
                
                if len(pdf_document) > 0:
                    first_page = pdf_document.load_page(0)
                    pix = first_page.get_pixmap(dpi=150) # Render page to an image
                    
                    # Save the image bytes to a buffer
                    img_buffer = io.BytesIO(pix.tobytes("png"))
                    
                    # Create a file name and save it to the cover_image field
                    file_name = f"{self.title.replace(' ', '_')}_cover.png"
                    self.cover_image.save(file_name, ContentFile(img_buffer.getvalue()), save=False)
                    return True
        except Exception:
            # Silently fail if there's an error processing the PDF
            pass
        return False

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically handle cover images.
        First, it saves the book (including the file). Then, if it's a new book
        without a cover, it tries to fetch or generate one and saves again.
        """
        # Determine if this is a new instance before the initial save.
        is_new_instance = self.pk is None

        # Perform the initial save. This is crucial for the file to exist on storage.
        super().save(*args, **kwargs)

        # If it's a new book and the user did not provide a cover, try to find/generate one.
        if is_new_instance and not self.cover_image:
            # Try fetching from Google, if that fails, try generating from PDF.
            if self.fetch_cover_from_google_books() or self.generate_cover_from_pdf():
                # If a cover was found, save the instance again, but only update the cover field
                # to prevent recursion and re-running the whole save method.
                super().save(update_fields=['cover_image'])

    def get_file_size(self):
        """Returns the file size in a human-readable format (KB, MB)."""
        try:
            if self.book_file and self.book_file.storage.exists(self.book_file.name):
                size = self.book_file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024**2:
                    return f"{size/1024:.1f} KB"
                else:
                    return f"{size/1024**2:.1f} MB"
        except (FileNotFoundError, ValueError):
            # If the file doesn't exist on storage, return None gracefully.
            return None
        return None
    get_file_size.short_description = 'File Size'
    
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
    admin_notes = models.TextField(blank=True, help_text="Notes on fulfillment, 'Sent via WhatsApp on 2025-10-23'.")

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

    def colored_status(self):
        """
        Displays the status field with a color for quick visual scanning.
        Green for fulfilled, Red for pending/rejected states.
        """
        if self.status == 'FULFILLED':
            color = 'green'
        elif self.status in ['PENDING', 'REJECTED', 'CONTACT']:
            color = 'red'
        else:
            color = 'black'  # Fallback

        return mark_safe(f'<b style="color: {color};">{self.get_status_display()}</b>')
    colored_status.short_description = 'Status'

    class Meta:
        ordering = ['request_date']
        verbose_name = "Book Request/Order"
        verbose_name_plural = "Book Requests/Orders"
