from django.contrib import admin
from django.utils import timezone
from django.db import models
from django.db.models.functions import Concat # Import Concat for robust string concatenation
from django.utils.html import format_html
from .models import RequesterProfile, BookAvailable, BookRequest

# Register your models
# We will use custom admin classes for these models

# --- Custom Admin for RequesterProfile ---
@admin.register(RequesterProfile)
class RequesterProfileAdmin(admin.ModelAdmin):
    list_display = ('whatsapp_name', 'whatsapp_number', 'user', 'is_active', 'joined_date')
    search_fields = ('whatsapp_name', 'whatsapp_number', 'user__username', 'user__email')
    list_filter = ('is_active', 'joined_date')
    # You could add inlines here to show related BookRequests if desired
    # inlines = [BookRequestInline]

# --- Custom Admin for BookAvailable ---
@admin.register(BookAvailable)
class BookAvailableAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'is_available', 'published_date')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('is_available', 'published_date')

# --- Custom Admin for BookRequest ---
@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = (
        'requester',
        'get_requested_book_display', # Use the custom method for clarity
        'colored_status', # Add the new colored status display
        'status', 
        'request_date', 
        'get_whatsapp_link' # Custom method from the model
    )
    list_editable = ('status',) # Make the status field directly editable in the list view
    list_filter = ('status', 'request_date')

    # Enhance search fields to include direct book title/author for unlinked requests
    search_fields = (
        'requester__whatsapp_name',
        'requester__whatsapp_number', # Allow searching by requester's number
        'book_requested__title',
        'book_requested__author',
        'book_title', # Search directly on the requested title if not linked
        'book_author' # Search directly on the requested author if not linked
    )
    readonly_fields = ('request_date', 'fulfillment_date', 'requester', 'book_title', 'book_author')

    # Organize the admin detail view for better clarity
    fieldsets = (
        ('Request Details', {
            'fields': ('requester', ('book_title', 'book_author'), 'status', 'request_date')
        }),
        ('Fulfillment (Admin Use)', {
            'fields': ('book_requested', 'fulfillment_date', 'admin_notes')
        }),
    )
    
    # Add a custom method to display the requested book details
    def get_requested_book_display(self, obj):
        """
        Displays the book title and author, prioritizing linked BookAvailable
        over the manually entered book_title/book_author.
        """
        if obj.book_requested:
            return f"{obj.book_requested.title} by {obj.book_requested.author}"
        return f"{obj.book_title} by {obj.book_author}" if obj.book_author else obj.book_title
    get_requested_book_display.short_description = 'Requested Book'
    get_requested_book_display.admin_order_field = 'book_title' # Allows sorting by this field
    
    @admin.display(description='Status', ordering='status')
    def colored_status(self, obj):
        """
        Displays the status field with a color for quick visual scanning.
        Green for fulfilled, Red for pending/rejected states.
        """
        if obj.status == 'FULFILLED':
            color = 'green'
        elif obj.status in ['PENDING', 'REJECTED', 'CONTACT']:
            color = 'red'
        else:
            color = 'black' # Fallback
        
        return format_html('<b style="color: {};">{}</b>', color, obj.get_status_display())

    # Add the custom action
    actions = ['mark_as_fulfilled']

    @admin.action(description='Mark selected requests as FULFILLED (Sent)')
    def mark_as_fulfilled(self, request, queryset):
        """
        Custom Admin Action to quickly mark selected requests as completed.
        """
        updated_count = queryset.filter(status__in=['PENDING', 'CONTACT']).update(
            status='FULFILLED',
            fulfillment_date=timezone.now(),
            admin_notes=Concat(
                models.F('admin_notes'),
                models.Value(f'\nAutomatically marked fulfilled by Admin on {timezone.now().date()}.'),
                output_field=models.TextField()
            )
        )
        self.message_user(
            request, 
            f'{updated_count} request(s) were successfully marked as Fulfilled and timestamped.'
        )

# --- END Custom Admin ---
