from django.contrib import admin
from django.utils import timezone
from django.db import models # <-- NECESSARY FIX: Import the models namespace for F() expression
from .models import RequesterProfile, BookAvailable, BookRequest

# Register your models
admin.site.register(RequesterProfile)
admin.site.register(BookAvailable)


# --- Custom Admin for BookRequest ---

@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = (
        'requester', 
        'book_requested', 
        'status', 
        'request_date', 
        'get_whatsapp_link' # Custom method from the model
    )
    list_filter = ('status', 'request_date')
    search_fields = ('requester__whatsapp_name', 'book_requested__title')
    readonly_fields = ('request_date', 'fulfillment_date')
    
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
            admin_notes=models.F('admin_notes') + f'\nAutomatically marked fulfilled by Admin on {timezone.now().date()}.'
        )
        self.message_user(
            request, 
            f'{updated_count} request(s) were successfully marked as Fulfilled and timestamped.'
        )

# --- END Custom Admin ---
